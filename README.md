# AI API Testing Agent (MVP)

A small local-first college project MVP:
- Reads an OpenAPI JSON file
- Uses Ollama locally if available to suggest test cases
- Validates test cases with Python before execution
- Executes requests only against the local demo API (`127.0.0.1:8000`)
- Validates status codes and basic JSON fields
- Uses a bounded feedback loop to add a follow-up test
- Displays results in Streamlit and exports JSON

## Requirements
- Python 3.10+
- Internet is not required at runtime except when installing packages or downloading Ollama/model.
- Ollama is optional: deterministic fallback tests still run if Ollama/model is unavailable.

## Windows setup (PowerShell)
Run these from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Terminal 1 — start the demo API:
```powershell
python -m uvicorn demo_api.main:app --reload
```
Open http://127.0.0.1:8000/docs to verify it works.

Terminal 2 — start the UI:
```powershell
streamlit run app.py
```
Open the local URL Streamlit prints, usually http://localhost:8501.

## Optional local AI
Install Ollama only if time and disk space permit. Pull one model only, e.g. `qwen2.5-coder:3b-instruct`.
Then the app will try `http://localhost:11434/api/generate`. If unavailable, it automatically uses deterministic fallback tests.
Do not download a model if disk space is critically low. The project MVP can still demonstrate the bounded agent workflow without the LLM; clearly label that in the report.

## Demo
1. Start API and UI.
2. Upload `examples/sample_openapi.json`.
3. Click **Run agent tests**.
4. Review test results, feedback decision, and JSON report.

## Safety limits
- Target host is fixed to `127.0.0.1:8000`.
- Only GET requests are enabled in this MVP.
- Maximum 8 requests per run; timeout is 3 seconds.
- No arbitrary code from the LLM is executed.
- LLM-generated test cases are parsed and validated before use.

## Current MVP limitations
- Supports basic OpenAPI JSON paths and GET endpoints.
- The included demo API has GET /users and GET /users/{user_id}.
- POST/PUT/DELETE, comprehensive schema validation, auth, and persistent history are not implemented in this emergency MVP.
- A full project can extend this MVP to support all HTTP methods in the approved architecture.
