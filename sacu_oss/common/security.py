from fastapi import Header, HTTPException
from .config import API_KEY

def require_api_key(x_api_key: str = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(401, "Invalid or missing X-API-Key")