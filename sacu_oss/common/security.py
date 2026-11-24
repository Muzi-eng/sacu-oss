from fastapi import Header, HTTPException

# Role-based API keys (Separation of Privilege)
API_KEYS = {
    "demo-internal-key": "gateway", # The Gateway uses this to talk to admins
    "admin-only-key": "admin"       # Admins use this for direct access
}

def require_api_key(x_api_key: str = Header(default=None)):
    if x_api_key not in API_KEYS:
        raise HTTPException(401, "Invalid or missing X-API-Key")
    return API_KEYS[x_api_key]