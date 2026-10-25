ADMINISTRATIONS = {
    "SZ": {"code": "ERS",  "port": 8001, "vat_rate": 0.15, "currency": "SZL"},
    "ZA": {"code": "SARS", "port": 8002, "vat_rate": 0.15, "currency": "ZAR"},
    "LS": {"code": "RSL",  "port": 8003, "vat_rate": 0.15, "currency": "LSL"},
}

TARIFF = {
    "17": (0.00, False),
    "22": (0.20, False),
    "61": (0.45, False),
    "62": (0.45, False),
    "93": (0.00, True),
}
DEFAULT_TARIFF = (0.10, False)

BORDER_POSTS = ["Ngwenya-Oshoek", "Matsapha", "Lavumisa", "Maseru-Bridge"]

API_KEY = "demo-internal-key"

TRADERS = {
    "ERS":  {"SZ-T001": "ACTIVE", "SZ-T003": "SUSPENDED"},
    "SARS": {"ZA-T001": "ACTIVE", "ZA-T002": "ACTIVE"},
    "RSL":  {"LS-T001": "ACTIVE"},
}