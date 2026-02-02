from fastapi import FastAPI, BackgroundTasks, Depends
from typing import Annotated, Any, Dict
from dotenv import load_dotenv

# Import Project Modules
from app.models import FinalCallbackPayload, ExtractedIntelligence
from app.internal.scanner import Scanner
from app.internal.llm_engine import LLMEngine
from app.internal.state_manager import StateManager
from app.utils.reporter import send_final_report
from app.dependencies import verify_api_key

load_dotenv()

app = FastAPI(title="Agentic Honey-Pot")

scanner = Scanner()
llm_engine = LLMEngine()
state_manager = StateManager()

@app.post("/honey-pot")
async def honey_pot_endpoint(
    # CHANGE: Accept raw dictionary to bypass validation errors
    raw_body: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    x_api_key: Annotated[str, Depends(verify_api_key)] 
):
    # --- 1. Manual Parsing (The "Fail-Safe" Way) ---
    
    # Handle sessionId vs sessionld (both spellings)
    session_id = raw_body.get("sessionId") or raw_body.get("sessionld") or "unknown_session"
    
    # Handle message (safely handle if it's a dict OR a string)
    msg_data = raw_body.get("message", {})
    if isinstance(msg_data, dict):
        incoming_text = msg_data.get("text", "")
    else:
        incoming_text = str(msg_data)
        
    # Handle history (safely ignore if missing)
    raw_history = raw_body.get("conversationHistory", [])
    clean_history = []
    if isinstance(raw_history, list):
        for h in raw_history:
            if isinstance(h, dict):
                clean_history.append(h)
            
    # --- 2. Core Logic ---
    current_session = state_manager.get_or_create_session(session_id)
    extracted_data = scanner.extract_intelligence(incoming_text)
    state_manager.update_state(session_id, extracted_data)
    current_session = state_manager.get_or_create_session(session_id)

    # Generate Reply
    reply_text = llm_engine.generate_reply(clean_history, incoming_text)

    # --- 3. Check Termination ---
    intel = current_session["intelligence"]
    has_critical_info = (len(intel["bankAccounts"]) > 0 or 
                         len(intel["upilds"]) > 0 or 
                         len(intel["phoneNumbers"]) > 0)
    
    should_report = (has_critical_info and current_session["turns"] >= 5) or (current_session["turns"] > 15)
    
    if should_report:
        final_payload = FinalCallbackPayload(
            sessionId=session_id,
            scamDetected=True,
            totalMessagesExchanged=current_session["turns"],
            extractedIntelligence=ExtractedIntelligence(
                bankAccounts=list(intel["bankAccounts"]),
                upilds=list(intel["upilds"]),
                phishingLinks=list(intel["phishingLinks"]),
                phoneNumbers=list(intel["phoneNumbers"]),
                suspiciousKeywords=list(intel["suspiciousKeywords"])
            ),
            agentNotes="Scammer engaged successfully."
        )
        background_tasks.add_task(send_final_report, final_payload)

    # --- 4. Return Plain JSON ---
    return {
        "status": "success",
        "reply": reply_text
    }

@app.get("/health")
def health_check():
    return {"status": "active"}
