from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

# 1. The Message Object (Crucial for handling the nested JSON)
class MessageObj(BaseModel):
    sender: Optional[str] = "unknown"
    text: str
    timestamp: Optional[Any] = 0  # set to Any to be safe against huge numbers

# 2. The Main Request Model
class IncomingRequest(BaseModel):
    # This config allows 'sessionId' OR 'sessionld' (typo) to work
    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    sessionId: str = Field(alias="sessionld", default="unknown_session")
    
    # IMPORTANT: Use the MessageObj here
    message: MessageObj
    
    conversationHistory: List[MessageObj] = []
    metadata: Optional[Dict[str, Any]] = {}

class ApiResponse(BaseModel):
    status: str = "success"
    reply: str

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = []
    upilds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    suspiciousKeywords: List[str] = []

class FinalCallbackPayload(BaseModel):
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str