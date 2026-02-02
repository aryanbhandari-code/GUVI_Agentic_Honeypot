import sqlite3
import json
from typing import Dict, Any, Set
from datetime import datetime

class StateManager:
    def __init__(self, db_path="honeypot.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Creates tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for Session Metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                turns INTEGER DEFAULT 0,
                scam_detected BOOLEAN DEFAULT 0,
                last_updated TEXT
            )
        ''')
        
        # Table for Intelligence (Stored as JSON strings)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intelligence (
                session_id TEXT PRIMARY KEY,
                bank_accounts TEXT DEFAULT '[]',
                upi_ids TEXT DEFAULT '[]',
                phishing_links TEXT DEFAULT '[]',
                phone_numbers TEXT DEFAULT '[]',
                suspicious_keywords TEXT DEFAULT '[]'
            )
        ''')
        conn.commit()
        conn.close()

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieves session state or creates a new one."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()

        if not row:
            # Create new session
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO sessions (session_id, turns, scam_detected, last_updated) VALUES (?, ?, ?, ?)",
                (session_id, 0, False, now)
            )
            # Initialize empty intelligence
            cursor.execute(
                "INSERT INTO intelligence (session_id) VALUES (?)", (session_id,)
            )
            conn.commit()
            return self._build_session_dict(session_id, 0, False, {})
        
        # Fetch intelligence
        cursor.execute("SELECT * FROM intelligence WHERE session_id = ?", (session_id,))
        intel_row = cursor.fetchone()
        conn.close()

        return self._build_session_dict(
            session_id, 
            row['turns'], 
            row['scam_detected'], 
            intel_row
        )

    def update_state(self, session_id: str, new_intel: Dict[str, Set[str]]):
        """Updates turn count and merges new intelligence."""
        # 1. Get current data to merge
        current = self.get_or_create_session(session_id)
        
        # 2. Increment turns
        new_turns = current['turns'] + 1
        
        # 3. Merge Sets (New + Old)
        updated_intel = {}
        for key in ['bankAccounts', 'upilds', 'phishingLinks', 'phoneNumbers', 'suspiciousKeywords']:
            # Convert list back to set, add new items, convert to list for storage
            old_set = set(current['intelligence'][key])
            new_set = new_intel.get(key, set())
            merged_list = list(old_set.union(new_set))
            updated_intel[key] = json.dumps(merged_list)

        # 4. Save to DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE sessions SET turns = ?, last_updated = ? WHERE session_id = ?",
            (new_turns, datetime.utcnow().isoformat(), session_id)
        )
        
        cursor.execute('''
            UPDATE intelligence SET 
                bank_accounts = ?, upi_ids = ?, phishing_links = ?, 
                phone_numbers = ?, suspicious_keywords = ?
            WHERE session_id = ?
        ''', (
            updated_intel['bankAccounts'], updated_intel['upilds'], 
            updated_intel['phishingLinks'], updated_intel['phoneNumbers'], 
            updated_intel['suspiciousKeywords'], session_id
        ))
        
        conn.commit()
        conn.close()

    def _build_session_dict(self, sid, turns, detected, intel_row) -> Dict:
        """Helper to format data exactly how main.py expects it."""
        # Handle case where intel_row might be a dict or sqlite3.Row
        def parse(key, col_name):
            val = intel_row[col_name] if intel_row else '[]'
            return set(json.loads(val))

        return {
            "session_id": sid,
            "turns": turns,
            "scam_detected": detected,
            "intelligence": {
                "bankAccounts": parse('bankAccounts', 'bank_accounts'),
                "upilds": parse('upilds', 'upi_ids'),
                "phishingLinks": parse('phishingLinks', 'phishing_links'),
                "phoneNumbers": parse('phoneNumbers', 'phone_numbers'),
                "suspiciousKeywords": parse('suspiciousKeywords', 'suspicious_keywords'),
            }
        }