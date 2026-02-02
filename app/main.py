from fastapi import FastAPI, BackgroundTasks, Depends
from typing import Annotated
from dotenv import load_dotenv

# Import Project Modules
from app.models import IncomingRequest, FinalCallbackPayload, ExtractedIntelligence
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
    request: IncomingRequest, 
    background_tasks: BackgroundTasks,
    x_api_key: Annotated[str, Depends(verify_api_key)] 
):
    # 1. Extract Data
    session_id = request.sessionId
    incoming_text = request.message.text
    
    # 2. Retrieve State
    current_session = state_manager.get_or_create_session(session_id)

    # 3. Analyze Message
    extracted_data = scanner.extract_intelligence(incoming_text)
    
    # 4. Update Database
    state_manager.update_state(session_id, extracted_data)
    current_session = state_manager.get_or_create_session(session_id)

    # 5. Generate Reply
    # Convert Pydantic objects to dicts for the LLM
    history_dicts = [h.model_dump() for h in request.conversationHistory]
    reply_text = llm_engine.generate_reply(history_dicts, incoming_text)

    # 6. Check Termination
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

    # Return plain dict for maximum compatibility with the Tester
    return {
        "status": "success",
        "reply": reply_text
    }

@app.get("/health")
def health_check():
    return {"status": "active"}