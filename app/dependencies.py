from fastapi import Header, HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

# Get the secret from your .env file
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "hackathon_default_secret")

async def verify_api_key(x_api_key: str = Header(...)):
    """
    This function acts as a 'Gatekeeper'.
    It runs automatically before every request to your API.
    If the key doesn't match, it blocks the request immediately.
    """
    if x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or Missing API Key")
    return x_api_key