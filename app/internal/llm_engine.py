import os
from groq import Groq
from typing import List, Dict

class LLMEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is missing in .env file")
        
        self.client = Groq(api_key=self.api_key)
        
        # THIS IS THE KEY FIX: Use the versatile model
        self.model = "llama-3.3-70b-versatile"

    def generate_reply(self, history: List[Dict], incoming_text: str) -> str:
        try:
            # System Prompt: Elderly Indian Grandmother Persona
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an elderly, confused, but wealthy Indian grandmother named 'Asha-ji'. "
                        "You are talking to a scammer. You want to waste their time. "
                        "Act interested but technically illiterate. Ask wrong questions. "
                        "Never give real passwords or OTPs. "
                        "Keep your replies short (under 2 sentences)."
                    )
                }
            ]

            # Add History
            for turn in history:
                role = "user" if turn.get("sender") == "scammer" else "assistant"
                messages.append({"role": role, "content": str(turn.get("text", ""))})

            # Add Current Message
            messages.append({"role": "user", "content": incoming_text})

            # Call Groq
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.7,
                max_tokens=150
            )

            return chat_completion.choices[0].message.content

        except Exception as e:
            print(f"LLM Error: {e}")
            return "Beta, I didn't understand. Can you explain again?"