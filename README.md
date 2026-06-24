# Ayurcare Agent - Ayurveda Health Guidance System

Ayurcare Agent is a serverless, multi-agent health-guidance system utilizing traditional Ayurveda principles. It is built with the Google Agent Development Kit (ADK), featuring a standalone Model Context Protocol (MCP) server, rigorous safety controls, and a React frontend.

---

## 1. Problem Statement
Many health systems lack structured wellness advice tailored to an individual’s physical constitution (Prakriti). Furthermore, generic AI health models present significant risks: they may recommend mild home remedies for emergency conditions (e.g., advising herbal tea for chest pain), prescribe precise dosages without clinical basis, or make unauthorized claims to cure diseases. Ayurcare Agent addresses this by utilizing a gated multi-agent workflow to conduct a friendly intake, determine constitution, fetch safe Ayurvedic knowledge, and review recommendations against strict medical red flags.

---

## 2. Why Agents? (vs. A Single LLM Call)
A single LLM call attempting to handle intake, Prakriti analysis, tool execution, formatting, and safety checks faces the following limitations:
- **Instruction Drift & Bloat:** As the prompt grows to accommodate all rules, the model is more likely to miss details (e.g., forgetting the disclaimer or ignoring a red flag symptom).
- **Security Risks:** System instructions can be leaked or overridden by prompt injection if the evaluation and sanitization stages are not isolated.
- **De-coupled Concerns:** Chaining specialized agents allows each model to focus on a singular goal with unique instructions, leading to higher reliability:
  - **Intake Agent:** Restricts itself to gathering demographics and lifestyle details without dispensing advice.
  - **Prakriti Agent:** Analyzes the structured intake JSON to determine the dosha.
  - **Knowledge Agent:** Interacts with the local MCP server database.
  - **Recommendation Agent:** Formulates the wellness copy in a humble, wellness-oriented tone.
  - **Safety Agent:** Evaluates the final advice with absolute veto power, ensuring clinical safety.

---

## 3. Architecture Diagram
```
              +-----------------------------------------+
              |               User Message              |
              +-----------------------------------------+
                                   |
                                   v
              +-----------------------------------------+
              |           Input Sanitizer               |
              | (Strips injection words from user text) |
              +-----------------------------------------+
                                   |
                                   v
              +-----------------------------------------+
              |          1. Intake Agent                |
              |  (Converses; asks 1 question at a time) |
              +-----------------------------------------+
                                   |
                       Intake JSON | (Cascades once intake is done)
                                   v
              +-----------------------------------------+
              |          2. Prakriti Agent              |
              | (Computes Vata / Pitta / Kapha scores)  |
              +-----------------------------------------+
                                   |
                      Prakriti JSON|
                                   v
              +-----------------------------------------+
              |          3. Knowledge Agent             |
              |      (Connects to MCP Server via        | <---+
              |        StdioConnectionParams)           |     |
              +-----------------------------------------+     | MCP Protocol
                                   |                          v
                     Raw retrieved |             +-------------------------+
                     Ayurveda data |             |       MCP Server        |
                                   v             |  (ayurveda_server.py)   |
              +-----------------------------------------+ |  Exposes:               |
              |        4. Recommendation Agent          | |  - check_red_flag      |
              | (Drafts diet/lifestyle/herb suggestions)| |  - get_dosha_info       |
              +-----------------------------------------+ |  - get_herb_recs        |
                                   |                      +-------------------------+
                      Unchecked rec|
                                   v
              +-----------------------------------------+
              |           5. Safety Agent               |
              |     - Red Flag Override: Vetoes and     |
              |       replaces with Emergency Alert     |
              |     - QA Clean: Strips herbal dosages   |
              |       and ensures wellness disclaimer   |
              +-----------------------------------------+
                                   |
                                   v
              +-----------------------------------------+
              |             Final Output                |
              |      (To Flask API / React Client)      |
              +-----------------------------------------+
```

---

## 4. Setup & Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+

### Step-by-Step Local Run

1. **Clone the Repository & Navigate:**
   ```bash
   cd C:/Users/UDISHA/.gemini/antigravity/scratch/ayurcare-agent
   ```

2. **Initialize Python Virtual Environment & Install Dependencies:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Setup Local Environment Variable:**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_actual_gemini_api_key_here
   ```
   *(Note: If the key is missing or if network connection fails, the application will automatically enter **Mock/Fallback Mode** utilizing the local JSON database, allowing offline testing).*

4. **Launch Backend and Frontend Simultaneously:**
   Ensure you have configured `frontend/.env.local` to point to the backend:
   ```env
   VITE_API_URL=http://127.0.0.1:5000
   ```
   To run both servers concurrently with a single command on Windows (PowerShell), execute:
   ```powershell
   Start-Process python -ArgumentList "api/agent.py"; cd frontend; npm run dev
   ```
   This will spin up the Flask backend in a separate terminal window and start the Vite React development server in your current window. Navigate to the local URL (usually `http://localhost:5173`) to interact with the application.

5. **Run Local Integration Tests:**
   You can verify the database tools and mock fallback pipeline end-to-end using:
   ```bash
   python scratch/test_pipeline.py
   ```

---

## 5. Deployment Steps (Vercel)

Ayurcare Agent is designed as a decoupled architecture: the Flask API deploys as Python serverless functions, and the React client deploys as a static static site.

### Backend API Deployment
1. Log in via Vercel CLI from the root folder:
   ```bash
   vercel login
   ```
2. Run initial deployment:
   ```bash
   vercel
   ```
3. Set the environment variable in your Vercel Project dashboard:
   - Name: `GOOGLE_API_KEY`
   - Value: `<your_gemini_api_key>`
4. Promote to production:
   ```bash
   vercel --prod
   ```
   *Take note of the deployed backend URL (e.g. `https://ayurcare-agent-api.vercel.app`).*

### Frontend Client Deployment
1. Navigate to the `frontend/` folder.
2. Initialize a new project on Vercel:
   ```bash
   vercel
   ```
3. Set the frontend environment variable in the Vercel dashboard:
   - Name: `VITE_API_URL`
   - Value: `<your_deployed_backend_url>`
4. Promote the client to production:
   ```bash
   vercel --prod
   ```

### Testing the Deployed API via curl
```bash
curl -X POST https://<your_deployed_backend_url>/api/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I have a persistent headache.", "session_id": "curl_session_id"}'
```

---

## 6. Course Concepts Demonstrated

- **Multi-Agent Orchestration via ADK:** Leverages the ADK `Workflow` engine to construct sequential and conditional execution graphs. It handles intermediate state preservation, allowing multiple non-interactive agents to execute in cascading succession during a single turn.
- **Model Context Protocol (MCP):** Implements a standalone MCP server (`ayurveda_server.py`) exposing custom Python tools. The `knowledge_agent` establishes dynamic process-based communication using `MCPToolset` and `StdioConnectionParams`.
- **Advanced Security Features:**
  - **Input Sanitization:** Intercepts prompt injection attacks inside the orchestrator using automated regex filters.
  - **Zero-Log Credential Policy:** Restricts API key retrieval exclusively to system environment variables and prevents printing keys in error traces.
  - **Rate Limiting:** Protects serverless resources with a rolling window rate-limiter (15 requests/minute).
  - **Safety-Gating (Safety Agent):** Enforces clinical boundary rules, overriding recommendations if a red-flag condition occurs.
- **Serverless-Optimized Design:** Implements lazy loading of ADK agents inside `api/agent.py` to minimize cold-start times when running on Vercel serverless containers.
