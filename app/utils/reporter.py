# app/utils/reporter.py
import requests
import logging
from app.models import FinalCallbackPayload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GUVI_ENDPOINT = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def send_final_report(payload: FinalCallbackPayload):
    try:
        response = requests.post(GUVI_ENDPOINT, json=payload.model_dump(), timeout=5)
        if response.status_code == 200:
            logger.info(f"SUCCESS: Report sent for {payload.sessionId}")
        else:
            logger.error(f"FAILED to send report: {response.text}")
    except Exception as e:
        logger.error(f"EXCEPTION sending report: {e}")