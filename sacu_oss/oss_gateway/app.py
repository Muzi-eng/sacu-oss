import json, secrets
from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import httpx
from ..common.config import ADMINISTRATIONS, BORDER_POSTS, API_KEY
from ..common.db import connect, now

class DeclarationIn(BaseModel):
    exporter_id: str
    importer_id: str
    origin_country: str
    destination_country: str
    border_post: str
    hs_code: str
    description: str
    quantity: float = Field(gt=0)
    customs_value: float = Field(gt=0)

class PaymentIn(BaseModel):
    amount: float
    method: str = "EFT"

app = FastAPI(title="SACU OSS Gateway")

# Mount static files for the web portal
app.mount("/static", StaticFiles(directory="sacu_oss/oss_gateway/static"), name="static")

conn = connect("GATEWAY")

class AdminError(Exception):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail

def call(admin_code: str, method: str, path: str, body: dict = None):
    cfg = next(v for v in ADMINISTRATIONS.values() if v["code"] == admin_code)
    url = f"http://127.0.0.1:{cfg['port']}{path}"
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.request(method, url, json=body, headers={"X-API-Key": API_KEY})
    except httpx.ConnectError:
        raise AdminError(502, f"{admin_code} unavailable")
    if r.status_code >= 400:
        raise AdminError(r.status_code, r.json().get("detail", "error"))
    return r.json()

def _init_gateway_db():
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS gateway_declarations (
            ucr TEXT PRIMARY KEY,
            idem_key TEXT UNIQUE,
            status TEXT,
            origin TEXT,
            destination TEXT,
            payload TEXT,
            assessment TEXT,
            receipt TEXT,
            release_codes TEXT,
            reason TEXT,
            created TEXT,
            updated TEXT
        );
    ''')
    conn.commit()
_init_gateway_db()

def update(ucr, **kw):
    fields = ", ".join(f"{k}=?" for k in kw)
    conn.execute(f"UPDATE gateway_declarations SET {fields}, updated=? WHERE ucr=?",
                 (*kw.values(), now(), ucr))
    conn.commit()

@app.get("/")
def root():
    """Serve the SACU One Stop Shop web portal."""
    return FileResponse("sacu_oss/oss_gateway/static/index.html")

@app.post("/api/v1/declarations", status_code=201)
def submit(req: DeclarationIn, idempotency_key: Optional[str] = Header(default=None)):
    if req.origin_country == req.destination_country:
        raise HTTPException(422, "Origin and destination must differ")
    if req.border_post not in BORDER_POSTS:
        raise HTTPException(422, f"Unknown border post {req.border_post}")
    if idempotency_key:
        existing = conn.execute(
            "SELECT ucr FROM gateway_declarations WHERE idem_key=?", (idempotency_key,)
        ).fetchone()
        if existing:
            return get_declaration(existing["ucr"])
    origin_code = ADMINISTRATIONS[req.origin_country]["code"]
    dest_code   = ADMINISTRATIONS[req.destination_country]["code"]
    ucr = f"UCR26{req.origin_country}{secrets.token_hex(4).upper()}"
    conn.execute(
        "INSERT INTO gateway_declarations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (ucr, idempotency_key, "SUBMITTED", origin_code, dest_code,
         req.model_dump_json(), None, None, None, None, now(), now()),
    )
    conn.commit()
    try:
        call(origin_code, "POST", "/api/v1/exports/validate",
             {"ucr": ucr, "trader_id": req.exporter_id,
              "hs_code": req.hs_code, "customs_value": req.customs_value})
        update(ucr, status="EXPORT_VALIDATED")
        assess = call(dest_code, "POST", "/api/v1/imports/assess",
                      {"ucr": ucr, "trader_id": req.importer_id,
                       "hs_code": req.hs_code, "customs_value": req.customs_value})
    except AdminError as e:
        status = "REJECTED" if e.code == 422 else "FAILED"
        update(ucr, status=status, reason=f"{e.code}: {e.detail}")
        raise HTTPException(e.code, e.detail)
    update(ucr, status="ASSESSED", assessment=json.dumps(assess["assessment"]))
    return {"ucr": ucr, "status": "ASSESSED", "origin": origin_code,
            "destination": dest_code, "hs_code": req.hs_code,
            "customs_value": req.customs_value,
            "assessment": assess["assessment"]}

@app.post("/api/v1/declarations/{ucr}/payments")
def pay(ucr: str, req: PaymentIn):
    row = conn.execute("SELECT * FROM gateway_declarations WHERE ucr=?", (ucr,)).fetchone()
    if not row:
        raise HTTPException(404, "Declaration not found")
    if row["status"] != "ASSESSED":
        raise HTTPException(409, f"Cannot pay in status {row['status']}")
    assessment = json.loads(row["assessment"])
    if abs(req.amount - assessment["total_payable"]) > 0.005:
        raise HTTPException(422, f"Amount must equal the assessed total of {assessment['total_payable']:.2f}")
    try:
        pay_resp = call(row["destination"], "POST", "/api/v1/payments",
                        {"ucr": ucr, "amount": req.amount, "method": req.method})
    except AdminError as e:
        raise HTTPException(e.code, e.detail)
    update(ucr, status="PAID", receipt=pay_resp["receipt"])
    return clear(ucr, row["origin"], row["destination"])

def clear(ucr, origin_code, dest_code):
    try:
        exp = call(origin_code, "POST", "/api/v1/release", {"ucr": ucr, "kind": "EXPORT"})
        imp = call(dest_code,   "POST", "/api/v1/release", {"ucr": ucr, "kind": "IMPORT"})
    except AdminError as e:
        update(ucr, status="RELEASE_PENDING", reason=f"{e.code}: {e.detail}")
        return get_declaration(ucr)
    update(ucr, status="CLEARED", reason=None,
           release_codes=json.dumps({"export": exp["release_code"],
                                     "import": imp["release_code"]}))
    return get_declaration(ucr)

@app.get("/api/v1/declarations")
def list_declarations():
    rows = conn.execute(
        "SELECT ucr, status, origin, destination, receipt, release_codes, created "
        "FROM gateway_declarations ORDER BY created DESC LIMIT 50"
    ).fetchall()
    return [dict(r) for r in rows]

@app.get("/api/v1/declarations/{ucr}")
def get_declaration(ucr: str):
    row = conn.execute("SELECT * FROM gateway_declarations WHERE ucr=?", (ucr,)).fetchone()
    if not row:
        raise HTTPException(404, "Declaration not found")
    return dict(row)

@app.post("/api/v1/declarations/{ucr}/clearance")
def retry_clearance(ucr: str):
    row = conn.execute("SELECT * FROM gateway_declarations WHERE ucr=?", (ucr,)).fetchone()
    if not row:
        raise HTTPException(404, "Declaration not found")
    if row["status"] != "RELEASE_PENDING":
        raise HTTPException(409, f"Declaration is not pending release ({row['status']})")
    return clear(ucr, row["origin"], row["destination"])

@app.get("/api/v1/admins/status")
def status():
    out = {}
    for code in ["ERS", "SARS", "RSL"]:
        try:
            call(code, "GET", "/health")
            out[code] = "UP"
        except Exception:
            out[code] = "DOWN"
    return out

@app.get("/api/v1/revenue/summary")
def revenue_summary():
    out = {}
    for code in ["ERS", "SARS", "RSL"]:
        try:
            out[code] = call(code, "GET", "/api/v1/revenue/summary")
        except Exception:
            out[code] = {"error": "unavailable"}
    return out