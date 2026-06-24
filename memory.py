import os
import json

HISTORY_FILE = "data/chat_history.json"

SESSION_MEMORY = {}

# Load session memory from JSON file on startup if it exists
if os.path.exists(HISTORY_FILE):
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            SESSION_MEMORY = json.load(f)
    except Exception as e:
        print(f"Error loading chat history: {e}")

def save_history():
    """Saves the conversation history to data/chat_history.json."""
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(SESSION_MEMORY, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def get_conversation_history(session_id: str) -> list:
    """Retrieves the full conversation history for a given session ID."""
    return SESSION_MEMORY.get(session_id, [])

def append_message(session_id: str, role: str, content: str):
    """Appends a new message to the conversation history of the given session ID and saves it to disk."""
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = []
    SESSION_MEMORY[session_id].append({
        "role": role,
        "content": content
    })
    save_history()

def get_recent_history(session_id: str, window: int = 6) -> list:
    """Retrieves the last `window` messages (sliding window) for the given session ID."""
    history = SESSION_MEMORY.get(session_id, [])
    return history[-window:]
