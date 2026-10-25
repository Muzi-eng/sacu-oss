import json, secrets
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from ..common.config import ADMINISTRATIONS, TARIFF, DEFAULT_TARIFF
from ..common.security import require_api_key
from ..common.db import connect, now

class ValidateIn(BaseModel):
    ucr: str
    trader_id: str
    hs_code: str
    customs_value: float = Field(gt=0)

class PaymentIn(BaseModel):
    ucr: str
    amount: float
    method: str = "EFT"

class ReleaseIn(BaseModel):
    ucr: str
    kind: str

def create_app(code: str):
    cfg = next(v for v in ADMINISTRATIONS.values() if v["code"] == code)
    app = FastAPI(title=f"{code} Administration Service")
    conn = connect(code)

    @app.get("/health")
    def health():
        return {"status": "ok", "admin": code}

    @app.get("/api/v1/traders/{trader_id}", dependencies=[Depends(require_api_key)])
    def get_trader(trader_id: str):
        row = conn.execute(
            "SELECT id, status FROM traders WHERE id=?", (trader_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, f"Trader {trader_id} not found")
        return {"id": row["id"], "status": row["status"]}

    @app.post("/api/v1/exports/validate", dependencies=[Depends(require_api_key)])
    def validate_export(req: ValidateIn):
        row = conn.execute(
            "SELECT status FROM traders WHERE id=?", (req.trader_id,)
        ).fetchone()
        if not row or row["status"] != "ACTIVE":
            raise HTTPException(422, f"Exporter {req.trader_id} is suspended with {code}")
        chapter = req.hs_code[:2]
        duty_rate, permit = TARIFF.get(chapter, DEFAULT_TARIFF)
        if permit:
            raise HTTPException(422, "Goods require an export permit; refer to a customs officer")
        conn.execute(
            "INSERT OR REPLACE INTO declarations VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (req.ucr, "EXPORT", req.trader_id, req.hs_code, req.customs_value,
             0, 0, 0, "VALIDATED", "{}", now()),
        )
        conn.commit()
        return {"status": "VALIDATED", "ucr": req.ucr}

    @app.post("/api/v1/imports/assess", dependencies=[Depends(require_api_key)])
    def assess_import(req: ValidateIn):
        row = conn.execute(
            "SELECT status FROM traders WHERE id=?", (req.trader_id,)
        ).fetchone()
        if not row or row["status"] != "ACTIVE":
            raise HTTPException(422, f"Importer {req.trader_id} is not active with {code}")
        chapter = req.hs_code[:2]
        duty_rate, permit = TARIFF.get(chapter, DEFAULT_TARIFF)
        if permit:
            raise HTTPException(422, "Goods require an import permit; refer to a customs officer")
        duty = round(req.customs_value * duty_rate, 2)
        vat  = round((req.customs_value + duty) * cfg["vat_rate"], 2)
        total = round(duty + vat, 2)
        conn.execute(
            "INSERT OR REPLACE INTO declarations VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (req.ucr, "IMPORT", req.trader_id, req.hs_code, req.customs_value,
             duty, vat, total, "ASSESSED", "{}", now()),
        )
        conn.commit()
        return {
            "status": "ASSESSED", "ucr": req.ucr,
            "assessment": {"duty_rate": duty_rate, "vat_rate": cfg["vat_rate"],
                           "duty": duty, "vat": vat, "total_payable": total,
                           "currency": cfg["currency"]},
        }

    @app.post("/api/v1/payments", dependencies=[Depends(require_api_key)])
    def record_payment(req: PaymentIn):
        row = conn.execute(
            "SELECT total, status FROM declarations WHERE ucr=? AND kind='IMPORT'",
            (req.ucr,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Declaration not found")
        if row["status"] in ("PAID", "CLEARED"):
            raise HTTPException(409, "Declaration already paid")
        if abs(req.amount - row["total"]) > 0.005:
            raise HTTPException(422, f"Amount must equal the assessed total of {row['total']:.2f}")
        receipt = f"{code}-RCPT-{secrets.token_hex(4).upper()}"
        conn.execute(
            "INSERT INTO payments VALUES (?,?,?,?,?,?,?)",
            (receipt, req.ucr, req.amount, req.method,
             row["total"] * 0.5263, row["total"] * 0.4737, now()),
        )
        conn.execute(
            "UPDATE declarations SET status='PAID' WHERE ucr=? AND kind='IMPORT'",
            (req.ucr,),
        )
        conn.commit()
        return {"status": "PAID", "receipt": receipt, "ucr": req.ucr}

    @app.post("/api/v1/release", dependencies=[Depends(require_api_key)])
    def release(req: ReleaseIn):
        row = conn.execute(
            "SELECT status FROM declarations WHERE ucr=? AND kind=?",
            (req.ucr, req.kind),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Declaration not found")
        if row["status"] == "RELEASED":
            return {"status": "RELEASED", "release_code": f"{code}-REL-DUP"}
        if req.kind == "IMPORT" and row["status"] != "PAID":
            raise HTTPException(409, "Payment required before import release")
        release_code = f"{code}-REL-{secrets.token_hex(4).upper()}"
        conn.execute(
            "UPDATE declarations SET status='RELEASED' WHERE ucr=? AND kind=?",
            (req.ucr, req.kind),
        )
        conn.commit()
        return {"status": "RELEASED", "release_code": release_code}

    @app.get("/api/v1/revenue/summary", dependencies=[Depends(require_api_key)])
    def revenue_summary():
        rows = conn.execute("SELECT amount FROM payments").fetchall()
        total = round(sum(r["amount"] for r in rows), 2)
        duty = round(total * 0.5263, 2)
        vat = round(total - duty, 2)
        return {"admin": code, "payments": len(rows), "total": total,
                "customs_duty": duty, "vat": vat}

    return app