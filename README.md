# AI API Testing Agent

A local-first Agentic AI project that automates REST API testing using an OpenAPI specification, a locally running LLM, deterministic Python tools, and a bounded feedback loop.

## Project Overview

The AI API Testing Agent reads an OpenAPI JSON specification, generates test cases, executes approved HTTP requests against a local FastAPI demo API, validates responses, and produces a structured test report.

The agent observes actual execution results and can decide whether an additional test is useful, demonstrating the workflow:

**Reason → Act → Observe → Analyze → Act Again**

## Features

- Parses OpenAPI JSON specifications.
- Generates test cases using a local Ollama model when available.
- Provides deterministic fallback test generation.
- Validates generated test cases before execution.
- Executes HTTP requests against the configured local demo API.
- Validates expected versus actual HTTP status codes and basic response data.
- Uses a bounded feedback loop to add relevant follow-up tests.
- Displays execution results through Streamlit.
- Exports structured JSON test reports.
- Includes basic automated tests using pytest.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core implementation |
| FastAPI | Local demo API |
| Ollama | Local LLM inference |
| Streamlit | User interface |
| Requests | HTTP communication |
| pytest | Automated testing |
| OpenAPI / JSON | API specification format |
| Git | Version control |

## Requirements

- Windows, Linux, or macOS with a compatible Python environment.
- Python 3.10 or later.
- Git (optional, for version control).
- Ollama and a downloaded model for local LLM-based test generation.

Ollama is optional. The deterministic fallback can generate tests when the model is unavailable or its output cannot be used.

Internet access is generally needed to install dependencies or download a model, but not for normal local execution after setup.

## Windows Installation

Open PowerShell in the project directory.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the automated tests

```powershell
python -m pytest -v
```

The current basic test suite contains three tests covering OpenAPI parsing, CRUD fallback test generation, and rejection of an unsupported HTTP method.

## Run the Application

### Terminal 1 — Start the FastAPI demo server

```powershell
python -m uvicorn demo_api.main:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

The demo API provides an interface for manually inspecting and testing its endpoints.

### Terminal 2 — Start the Streamlit application

Activate the same virtual environment and run:

```powershell
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually:

http://localhost:8501

### Run the agent

1. Upload `examples/sample_openapi.json`.
2. Enable local Ollama test generation if desired.
3. Enter an installed Ollama model name, such as `llama3.2:3b`.
4. Click **Run agent tests**.
5. Inspect the generated tests, actual responses, PASS/FAIL results, and feedback decision.
6. Download the JSON report.

## Local LLM Setup

Install Ollama from https://ollama.com/ if it is not already installed.

For the model used during development:

```powershell
ollama pull llama3.2:3b
```

The application communicates with the local Ollama API. Model availability, generation quality, and output validation can affect whether the application uses LLM-generated tests or deterministic fallback tests.

No paid AI API is required.

## Architecture and Workflow

1. **Specification Parser:** Reads API paths, HTTP methods, parameters, and response information.
2. **AI Testing Agent:** Requests suitable test cases from the local LLM or uses deterministic fallback generation.
3. **Test Case Validator:** Checks generated test cases against the supported operations and safety rules.
4. **API Execution Engine:** Sends approved HTTP requests to the local demo API.
5. **Response Validator:** Compares actual responses with expected conditions.
6. **Feedback Loop:** Uses execution results to decide whether a bounded follow-up test is useful.
7. **Reporting Module:** Displays the results and produces a JSON report.

## Safety Controls

- API execution is restricted to the configured local demo target.
- Request timeouts and execution limits help prevent runaway testing.
- Generated test cases are validated before execution.
- The LLM does not execute arbitrary Python code or shell commands.
- Destructive operations should only be demonstrated against the local demo API.
- Generated expectations are not automatically treated as ground truth; they should be checked against the specification and API behavior.

## Verification Results

During development, the following results were observed:

- The basic pytest suite passed all three tests after the test fixture was updated.
- The deterministic fallback run executed six CRUD test cases, with all six passing.
- A local Ollama run generated test cases, and a bounded feedback run added a missing-ID test that received the expected HTTP 404 response.

These are development-run results, not a guarantee that every API or generated test will work correctly.

## Current Limitations

- OpenAPI parsing and response validation cover a limited subset of the full specifications.
- The local LLM may generate incomplete or incorrect test expectations.
- Test coverage varies between runs, especially when using an LLM.
- The current automated unit-test suite is small and does not establish complete end-to-end reliability.
- Authentication, comprehensive schema validation, persistent test history, and broad compatibility with arbitrary APIs are not established features of this MVP.
- The application is intended for local demonstration, not unrestricted production API testing.

## Future Improvements

- Expand OpenAPI schema and parameter validation.
- Add broader automated integration tests.
- Improve structured LLM output validation and failure diagnostics.
- Support more complex API workflows and test dependencies.
- Add persistent test history and richer reports.

## Project Objective

This project demonstrates how a local LLM can work with deterministic Python tools, real HTTP execution, response validation, and feedback-driven decisions to automate parts of REST API testing without requiring paid AI APIs.
