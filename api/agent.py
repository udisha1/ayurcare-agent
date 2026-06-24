from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import re
import json
import asyncio
from time import time
from dotenv import load_dotenv
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Configure CORS to allow access from local/remote frontend origins
CORS(app)

# In-memory session and rate-limit storage
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

@app.route("/api/agent", methods=["POST"])
def handle_agent():
    # 1. Rate limiting check
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if is_rate_limited(client_ip):
        return jsonify({"error": "Rate limit exceeded. Please try again in a minute."}), 429

    # 2. Parse request data
    data = request.get_json() or {}
    message_text = data.get("message", "").strip()
    session_id = data.get("session_id", "").strip()

    if not message_text or not session_id:
        return jsonify({"error": "Missing required fields: 'message' and 'session_id'."}), 400

    # 3. Input Sanitization
    from agents.orchestrator import sanitize_input
    sanitized_message = sanitize_input(message_text)

    # Initialize session store if not exists
    if session_id not in session_store:
        session_store[session_id] = {
            "messages": [],
            "is_mock": False,
            "mock_step": 0,
            "symptoms": "",
            "duration": "",
            "age_range": "",
            "lifestyle": "",
            "dosha_state": None
        }

    # Store message in history (to support fallback state construction)
    session_store[session_id]["messages"].append(sanitized_message)

    # 4. Check for Mock Mode condition
    # If the API key is missing or if the session has already encountered errors, use Mock Mode
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    use_mock = not api_key or session_store[session_id]["is_mock"]

    if use_mock:
        from agents.orchestrator import run_mock_workflow
        # Run local rule-based mock pipeline
        reply = run_mock_workflow(session_store[session_id], sanitized_message)
        return jsonify({
            "reply": reply,
            "dosha_state": session_store[session_id]["dosha_state"]
        }), 200

    # 5. Execute agent Workflow asynchronously (Live Mode)
    runner = get_runner()
    
    async def run_workflow():
        from google.genai import types
        
        # Ensure session exists in the ADK runner
        try:
            await runner.session_service.create_session(
                app_name=runner.app_name or "ayurcare",
                user_id=session_id,
                session_id=session_id
            )
        except Exception:
            pass

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
        # Gracefully handle API ClientError, ServerError, Connection errors, or quota exhaustion (429)
        app.logger.warning(f"Live agent execution failed ({type(e).__name__}). Falling back to Mock Mode.")
        
        # Switch session to Mock Mode for subsequent turns
        session_store[session_id]["is_mock"] = True
        
        # Sync the conversational state from history
        history = session_store[session_id]["messages"]
        session_store[session_id]["symptoms"] = history[0] if len(history) > 1 else ""
        session_store[session_id]["lifestyle"] = history[1] if len(history) > 2 else ""
        session_store[session_id]["age_range"] = history[2] if len(history) > 3 else ""
        session_store[session_id]["duration"] = history[3] if len(history) > 4 else ""
        session_store[session_id]["mock_step"] = len(history) - 1
        
        # Run mock workflow for the current turn
        from agents.orchestrator import run_mock_workflow
        reply = run_mock_workflow(session_store[session_id], sanitized_message)
        
        # Return clean 200 OK to keep frontend functional
        return jsonify({
            "reply": reply,
            "dosha_state": session_store[session_id]["dosha_state"]
        }), 200

    # Extract final safety agent response (excluding intermediate JSON objects)
    clean_reply = reply
    clean_reply = re.sub(r"```json\s*\{.*?\}\s*```", "", clean_reply, flags=re.DOTALL).strip()
    clean_reply = re.sub(r"\{.*?\}", "", clean_reply, flags=re.DOTALL).strip()
    if not clean_reply:
        clean_reply = reply.strip()

    return jsonify({
        "reply": clean_reply,
        "dosha_state": session_store[session_id]["dosha_state"]
    }), 200

def load_ayurveda_knowledge():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(current_dir, "..", "data", "ayurveda_knowledge.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_pdf(session_id, session_data):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Title
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, 750, "PranaAI Weekly Wellness Report")
    
    # Line separator
    p.setStrokeColorRGB(0.2, 0.56, 0.38) # nature green
    p.setLineWidth(2)
    p.line(50, 735, 550, 735)
    
    # Metadata
    p.setFont("Helvetica", 10)
    p.drawString(50, 715, f"Session ID: {session_id}")
    
    # Section 1: Dosha Profile
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 680, "1. Dosha Profile")
    
    dosha_state = session_data.get("dosha_state", {})
    dominant_dosha = dosha_state.get("dominant_dosha", "N/A")
    constitution = dosha_state.get("constitution_breakdown", {})
    reasoning = dosha_state.get("reasoning", "")
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, 655, f"Dominant Dosha: {dominant_dosha}")
    
    p.setFont("Helvetica", 11)
    y = 635
    p.drawString(60, y, "Constitution Breakdown:")
    y -= 18
    for d, val in constitution.items():
        p.drawString(80, y, f"- {d}: {val}")
        y -= 16
        
    y -= 10
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "2. Clinical Reasoning & Context")
    y -= 20
    p.setFont("Helvetica-Oblique", 11)
    
    # Wrap reasoning
    reasoning_lines = []
    words = reasoning.split(" ")
    current_line = ""
    for w in words:
        if len(current_line + " " + w) < 90:
            current_line += (" " if current_line else "") + w
        else:
            reasoning_lines.append(current_line)
            current_line = w
    if current_line:
        reasoning_lines.append(current_line)
        
    for line in reasoning_lines:
        p.drawString(60, y, line)
        y -= 16
        
    # Load knowledge base guidelines
    y -= 15
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "3. Recommended Diet & Lifestyle Guidelines")
    y -= 20
    
    try:
        kb = load_ayurveda_knowledge()
        matching_doshas = [d for d in ["Vata", "Pitta", "Kapha"] if d.lower() in dominant_dosha.lower()]
        if not matching_doshas:
            matching_doshas = ["Vata"] # fallback
            
        p.setFont("Helvetica", 11)
        for d in matching_doshas:
            guidance = kb["doshas"][d]["guidance"]
            charac = kb["doshas"][d]["characteristics"]
            
            p.setFont("Helvetica-Bold", 11)
            p.drawString(60, y, f"[{d} Balancing Guidelines]")
            y -= 18
            
            p.setFont("Helvetica", 11)
            # Wrap guidance
            words = guidance.split(" ")
            current_line = ""
            for w in words:
                if len(current_line + " " + w) < 90:
                    current_line += (" " if current_line else "") + w
                else:
                    p.drawString(70, y, current_line)
                    y -= 16
                    current_line = w
            if current_line:
                p.drawString(70, y, current_line)
                y -= 16
                
            y -= 10
            # Wrap characteristics
            p.setFont("Helvetica-Oblique", 10)
            words = charac.split(" ")
            current_line = ""
            for w in words:
                if len(current_line + " " + w) < 95:
                    current_line += (" " if current_line else "") + w
                else:
                    p.drawString(70, y, current_line)
                    y -= 14
                    current_line = w
            if current_line:
                p.drawString(70, y, current_line)
                y -= 14
            y -= 15
    except Exception as e:
        p.drawString(60, y, "Unable to load detailed guidelines from database.")
        y -= 16
        
    # Footer
    p.setFont("Helvetica-Bold", 10)
    p.setFillColorRGB(0.7, 0.3, 0.3)
    p.drawString(50, 60, "Disclaimer: This is traditional Ayurvedic wellness guidance, not a medical diagnosis or treatment plan.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

@app.route("/api/download_report", methods=["GET"])
def download_report():
    session_id = request.args.get("session_id")
    if not session_id or session_id not in session_store:
        return jsonify({"error": "Session not found."}), 404
        
    session_data = session_store[session_id]
    if not session_data.get("dosha_state"):
        return jsonify({"error": "No wellness report generated yet for this session."}), 404
        
    try:
        pdf_buffer = generate_pdf(session_id, session_data)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="PranaAI_Wellness_Report.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        app.logger.error(f"Error generating PDF: {str(e)}")
        return jsonify({"error": "Failed to generate report PDF."}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
