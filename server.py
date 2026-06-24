# pyrefly: ignore [missing-import]
from fastapi import FastAPI, WebSocket
# pyrefly: ignore [missing-import]
from starlette.websockets import WebSocketDisconnect 
import asyncio
import re
import time
import os
import json
from datetime import datetime
# pyrefly: ignore [missing-import]
import httpx

app = FastAPI()

from memory import append_message, get_recent_history, SESSION_MEMORY

def log_query(query: str, response_data: dict, latency: float):
    """Logs the query, response, and search latency to a log file."""
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/queries.log", "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "query": query,
                "latency_sec": round(latency, 4),
                "response": response_data
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Error writing to query log: {e}")

class SearchService:
    """Service to handle codebase search logic using the GraphRAG backend."""
    def __init__(self):
        pass

    async def search(self, query: str, history: list) -> str:
        """Queries the GraphRAG backend at http://localhost:8000/query."""
        # Try to parse the input as JSON to detect JSON-based client contract
        is_json_client = False
        query_text = query
        try:
            message_json = json.loads(query)
            if isinstance(message_json, dict) and "query" in message_json:
                query_text = message_json["query"]
                is_json_client = True
        except json.JSONDecodeError:
            pass

        # Start timing search latency
        start_time = time.perf_counter()

        # Connect to real GraphRAG backend
        status = "success"
        answer_text = ""
        sources = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://192.168.1.8:8000/query",
                    json={"repository": "ACIS", "query": query_text},
                    timeout=15.0
                )
                response.raise_for_status()
                data = response.json()
                answer_text = data.get("answer", "")
                sources = data.get("sources", [])
        except Exception as e:
            status = "error"
            answer_text = f"Error: Failed to retrieve answer from GraphRAG backend. Details: {e}"
            sources = []

        # Stop timing search latency
        end_time = time.perf_counter()
        latency = end_time - start_time

        # Format and log the response
        if is_json_client:
            response_data = {
                "query": query_text,
                "status": status,
                "answer": answer_text,
                "sources": sources
            }
            answer = json.dumps(response_data)
        else:
            # Return human-readable formatted string for display-only clients
            if status == "success":
                sources_text = ""
                if sources:
                    sources_text = "\n\nSources:\n" + "\n".join(f"- {s}" for s in sources)
                
                response = (
                    "==================================================\n"
                    "        CODE QUERY ASSISTANT - SEARCH RESULT      \n"
                    "==================================================\n"
                    f"Query: \"{query_text}\"\n\n"
                    f"{answer_text}{sources_text}\n"
                    "=================================================="
                )
            else:
                response = (
                    "==================================================\n"
                    "        CODE QUERY ASSISTANT - ERROR              \n"
                    "==================================================\n"
                    f"{answer_text}\n"
                    "=================================================="
                )
            answer = response
            
            # For logging purposes, we still want a structured dict
            response_data = {
                "query": query_text,
                "status": status,
                "answer": answer_text,
                "sources": sources,
                "search_latency_sec": round(latency, 4),
                "text_response": answer
            }

        # Log query to file
        log_query(query_text, response_data, latency)

        return answer

# Instantiate search service
search_service = SearchService()

@app.websocket("/query")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id")
    print(f"Session ID: {session_id}")

    try:
        while True:
            # Receive raw message from client
            query = await websocket.receive_text()
            print(f"[RECEIVED] Raw message: {query}")

            append_message(
                session_id,
                "user",
                query
            )

            history = get_recent_history(
                session_id,
                window=6
            )

            answer = await search_service.search(
                query=query,
                history=history
            )

            append_message(
                session_id,
                "assistant",
                answer
            )

            await websocket.send_text(answer)
            
            # Print session statistics and the full memory state
            print(f"Session {session_id}: {len(SESSION_MEMORY.get(session_id, []))} messages")
            print(SESSION_MEMORY)

    except WebSocketDisconnect:
        print("Client Disconnected")

    except WebSocketDisconnect:
        print("Client Disconnected")

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    # Listen on all interfaces (0.0.0.0) at port 8080 to accept local network connections
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
