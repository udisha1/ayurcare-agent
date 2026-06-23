# Ayurcare Agent

A multi-agent health-guidance system utilizing Ayurveda principles, built with the Google Agent Development Kit (ADK) and structured serverless deployments.

## Directory Structure
- `agents/`: Contains the individual ADK agents (`intake_agent.py`, `prakriti_agent.py`, `knowledge_agent.py`, `recommendation_agent.py`, `safety_agent.py`) and the `orchestrator.py` workflow.
- `mcp_server/`: Standalone Model Context Protocol (MCP) server `ayurveda_server.py` exposing Ayurveda knowledge retrieval tools.
- `data/`: Curated JSON knowledge base (`ayurveda_knowledge.json`).
- `api/`: Vercel serverless Flask entrypoint (`agent.py`).
- `frontend/`: React + Vite client chat interface.
- `scratch/`: Local test and interactive execution runners.

---

## Local Setup & Development

1. **Clone & Navigate:**
   ```bash
   cd C:/Users/UDISHA/.gemini/antigravity/scratch/ayurcare-agent
   ```

2. **Create and Activate Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment:**
   Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Add your Gemini API Key
   GOOGLE_API_KEY=AIzaSy...
   ```

5. **Run Standalone MCP Server (Local testing):**
   ```bash
   python mcp_server/ayurveda_server.py
   ```

6. **Run Interactive CLI Pipeline:**
   ```bash
   python scratch/run_interactive.py
   ```

7. **Start Local Flask API:**
   ```bash
   python api/agent.py
   ```

---

## Backend Deployment (Vercel API)

The `api/` folder is configured via `vercel.json` to deploy as a Python serverless function:

1. **Deploy using Vercel CLI:**
   From the project root:
   ```bash
   vercel
   ```

2. **Configure Environment Variables in Vercel Dashboard:**
   Add `GOOGLE_API_KEY` under Project Settings -> Environment Variables.

3. **Promote to Production:**
   ```bash
   vercel --prod
   ```
   Note the generated backend URL (e.g. `https://ayurcare-agent-backend.vercel.app`).

---

## Frontend Setup & Deployment (Vercel Client)

The React client located in `frontend/` should be deployed as its own separate Vercel project:

1. **Local Setup:**
   ```bash
   cd frontend
   npm install
   ```
   Create a `frontend/.env.local` containing:
   ```env
   VITE_API_URL=http://127.0.0.1:5000
   ```
   Run the local client:
   ```bash
   npm run dev
   ```

2. **Vercel Client Deployment:**
   Deploy `frontend/` as a separate project on Vercel:
   - Select the `frontend/` directory during import in the Vercel dashboard.
   - Configure the environment variable:
     - Name: `VITE_API_URL`
     - Value: `<your-backend-vercel-url>` (e.g., `https://ayurcare-agent-backend.vercel.app`)

---

## Testing Backend Endpoint with curl

You can verify the backend deployment by making a POST request to `/api/agent`:

```bash
curl -X POST https://<your-backend-vercel-url>/api/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I have a persistent headache.", "session_id": "test_curl_session"}'
```

Expected response format:
```json
{
  "reply": "Hello! I am sorry to hear you are dealing with a persistent headache. To help guide you safely, could you let me know how long you have had this headache?",
  "dosha_state": null
}
```
If the intake completes and Prakriti analysis fires, `dosha_state` will be populated with the parsed constitution profile.
