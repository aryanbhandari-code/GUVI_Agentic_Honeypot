# app/internal/scanner.py
import re
from typing import Dict, List

class Scanner:
    def __init__(self):
        # Patterns for extraction
        self.upi_pattern = r"[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}"
        self.bank_pattern = r"\b\d{9,18}\b"
        self.url_pattern = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
        self.phone_pattern = r"(\+91[\-\s]?)?[6-9]\d{9}"
        
        # Keywords that indicate a scam
        self.scam_keywords = [
            "blocked", "kyc", "verify", "suspend", "urgent", "otp", 
            "lottery", "winner", "refund", "electricity", "disconnection"
        ]

    def detect_scam(self, text: str) -> bool:
        """Simple keyword-based detection for low latency."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.scam_keywords)

    def extract_intelligence(self, text: str) -> Dict[str, List[str]]:
        """Extracts entities using Regex."""
        return {
            "bankAccounts": re.findall(self.bank_pattern, text),
            "upilds": re.findall(self.upi_pattern, text),
            "phishingLinks": re.findall(self.url_pattern, text),
            "phoneNumbers": re.findall(self.phone_pattern, text),
            "suspiciousKeywords": [kw for kw in self.scam_keywords if kw in text.lower()]
        }