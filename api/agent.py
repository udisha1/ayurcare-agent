from flask import Flask, request, jsonify
import os
import re
import json
import asyncio
from time import time

app = Flask(__name__)

# Simple in-memory session and rate-limit storage
session_store = {}
ip_request_history = {}

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 15  # requests per minute

# Lazy-loaded runner reference
_runner = None

def get_runner():
    global _runner
    if _runner is None:
        # Lazy load to keep serverless cold start fast
        from google.adk.runners import InMemoryRunner
        from agents.orchestrator import root_agent
        _runner = InMemoryRunner(agent=root_agent)
    return _runner

def is_rate_limited(ip: str) -> bool:
    now = time()
    if ip not in ip_request_history:
        ip_request_history[ip] = []
    
    # Filter timestamps to keep only those in current window
    ip_request_history[ip] = [t for t in ip_request_history[ip] if now - t < RATE_LIMIT_WINDOW]
    
    if len(ip_request_history[ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return True
    
    ip_request_history[ip].append(now)
    return False

@app.after_request
def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    return response

@app.route("/api/agent", methods=["OPTIONS"])
def handle_options():
    return "", 204

@app.route("/api/agent", methods=["POST"])
def handle_agent():
    # 1. Rate limiting check
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if is_rate_limited(client_ip):
        return jsonify({"error": "Rate limit exceeded. Please try again in a minute."}), 429

    # 2. API Key verification (never hardcoded, never logged)
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "API Key is not configured. Please contact the administrator."}), 500

    # 3. Parse request data
    data = request.get_json() or {}
    message_text = data.get("message", "").strip()
    session_id = data.get("session_id", "").strip()

    if not message_text or not session_id:
        return jsonify({"error": "Missing required fields: 'message' and 'session_id'."}), 400

    # 4. Input Sanitization
    from agents.orchestrator import sanitize_input
    sanitized_message = sanitize_input(message_text)

    # Initialize session store
    if session_id not in session_store:
        session_store[session_id] = {
            "dosha_state": None
        }

    # 5. Execute agent Workflow asynchronously
    runner = get_runner()
    
    async def run_workflow():
        from google.genai import types
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=sanitized_message)]
        )
        
        response_text = ""
        async for event in runner.run_async(
            user_id=session_id,
            session_id=session_id,
            new_message=content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        text = part.text
                        response_text += text
                        
                        # Extract prakriti_agent's JSON output if emitted
                        if '"dominant_dosha"' in text:
                            try:
                                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                                if json_match:
                                    prakriti_data = json.loads(json_match.group(0))
                                    session_store[session_id]["dosha_state"] = prakriti_data
                            except Exception:
                                pass
        return response_text

    try:
        reply = asyncio.run(run_workflow())
    except Exception as e:
        # Log generic error message without disclosing sensitive configuration values
        app.logger.error(f"Error executing ADK agents: {type(e).__name__}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

    # Extract final safety agent response (excluding intermediate JSON objects)
    # If the workflow outputs multiple steps, the final response is the text guide.
    # Let's clean up any intermediate json dumps from the final response text
    clean_reply = reply
    # Remove any markdown json blocks that represent the raw prakriti JSON or intake JSON
    clean_reply = re.sub(r"```json\s*\{.*?\}\s*```", "", clean_reply, flags=re.DOTALL).strip()
    clean_reply = re.sub(r"\{.*?\}", "", clean_reply, flags=re.DOTALL).strip()
    # Fallback to full reply if cleaning resulted in empty string
    if not clean_reply:
        clean_reply = reply.strip()

    return jsonify({
        "reply": clean_reply,
        "dosha_state": session_store[session_id]["dosha_state"]
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)
