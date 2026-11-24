import httpx

BASE = "http://127.0.0.1:8000"

def submit():
    r = httpx.post(f"{BASE}/api/v1/declarations", json={
        "exporter_id": "SZ-T001", "importer_id": "ZA-T001",
        "origin_country": "SZ", "destination_country": "ZA",
        "border_post": "Ngwenya-Oshoek", "hs_code": "220290",
        "description": "Beverage syrup", "quantity": 25, "customs_value": 480000,
    }, headers={"Idempotency-Key": "demo-key-001"})
    d = r.json()
    print(f"1. ASSESSED  ucr={d['ucr']}  total={d['assessment']['total_payable']} {d['assessment']['currency']}")
    return d["ucr"]

def pay(ucr):
    r = httpx.post(f"{BASE}/api/v1/declarations/{ucr}/payments",
                   json={"amount": 182400.0, "method": "EFT"})
    d = r.json()
    print(f"2. {d['status']}  receipt={d.get('receipt')}  releases={d.get('release_codes')}")

def negative_cases():
    r = httpx.post(f"{BASE}/api/v1/declarations", json={
        "exporter_id": "SZ-T003", "importer_id": "ZA-T001",
        "origin_country": "SZ", "destination_country": "ZA",
        "border_post": "Ngwenya-Oshoek", "hs_code": "220290",
        "description": "Test", "quantity": 1, "customs_value": 1000,
    })
    print(f"3a. REJECTED  {r.json().get('detail')}")
    r = httpx.post(f"{BASE}/api/v1/declarations", json={
        "exporter_id": "SZ-T001", "importer_id": "ZA-T001",
        "origin_country": "SZ", "destination_country": "ZA",
        "border_post": "Ngwenya-Oshoek", "hs_code": "930100",
        "description": "Test", "quantity": 1, "customs_value": 1000,
    })
    print(f"3b. REFERRED  {r.json().get('detail')}")

def revenue():
    d = httpx.get(f"{BASE}/api/v1/revenue/summary").json()
    print(f"4. REVENUE  {d}")

if __name__ == "__main__":
    ucr = submit()
    pay(ucr)
    negative_cases()
    revenue()