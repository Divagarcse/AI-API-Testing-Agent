import json
import re
import time
import requests

BASE_URL = "http://127.0.0.1:8000"
ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE"}
MAX_REQUESTS = 8
TIMEOUT_SECONDS = 3

def parse_openapi(spec):
    if not isinstance(spec, dict) or not isinstance(spec.get("paths"), dict):
        raise ValueError("Invalid OpenAPI JSON: expected an object with a 'paths' object.")
    endpoints = []
    for path, path_item in spec["paths"].items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method = method.upper()
            if method in {"GET", "POST", "PUT", "DELETE", "PATCH"} and isinstance(operation, dict):
                endpoints.append({
                    "path": path, "method": method, "summary": operation.get("summary", ""),
                    "parameters": operation.get("parameters", []),
                    "requestBody": operation.get("requestBody", {}),
                    "responses": operation.get("responses", {})
                })
    return endpoints

def fallback_cases(endpoints):
    available = {(e["path"], e["method"]) for e in endpoints}
    cases = []
    def add(test_id, endpoint, method, params, expected, fields=None, body=None, kind="positive"):
        cases.append({"test_id":test_id,"endpoint":endpoint,"method":method,"path_params":params,
                      "expected_status":expected,"required_fields":fields or [],"body":body,
                      "test_type":kind,"source":"deterministic_fallback"})
    if ("/users", "GET") in available:
        add("TC001", "/users", "GET", {}, 200)
    if ("/users/{user_id}", "GET") in available:
        add("TC002", "/users/{user_id}", "GET", {"user_id":1}, 200, ["id","name"])
        add("TC003", "/users/{user_id}", "GET", {"user_id":999}, 404, kind="negative")
    if ("/users", "POST") in available:
        add("TC004", "/users", "POST", {}, 201, ["id","name"], {"name":"Agent Test User"})
    if ("/users/{user_id}", "PUT") in available:
        add("TC005", "/users/{user_id}", "PUT", {"user_id":3}, 200, ["id","name"], {"name":"Updated Agent User"})
    if ("/users/{user_id}", "DELETE") in available:
        add("TC006", "/users/{user_id}", "DELETE", {"user_id":3}, 204, kind="destructive_local_demo")
    return cases


def _safe_case(case, endpoints):
    if not isinstance(case, dict):
        return False

    method = str(case.get("method", "")).upper()
    endpoint = case.get("endpoint")

    if method not in ALLOWED_METHODS:
        return False

    if not isinstance(endpoint, str):
        return False

    if (
        not endpoint.startswith("/")
        or "://" in endpoint
        or ".." in endpoint
        or endpoint.startswith("//")
    ):
        return False

    if not isinstance(case.get("path_params", {}), dict):
        return False

    operation = next(
        (
            item for item in endpoints
            if item["path"] == endpoint
            and item["method"] == method
        ),
        None,
    )

    if operation is None:
        return False

    # The LLM cannot invent expected status codes.
    responses = operation.get("responses", {})
    expected = str(case.get("expected_status", ""))

    if expected not in responses:
        return False

    return True



def ollama_cases(endpoints, model):
    prompt = f"""
You are an API testing assistant.

Generate up to 4 useful REST API test cases using only
the following OpenAPI operations:

{json.dumps(endpoints)}

Return ONLY a valid JSON object in this exact structure:
{{
  "tests": [
    {{
      "test_id": "AI001",
      "endpoint": "/users",
      "method": "GET",
      "path_params": {{}},
      "expected_status": 200,
      "required_fields": [],
      "body": null,
      "test_type": "positive"
    }}
  ]
}}

Rules:
- Use only paths and HTTP methods listed in the operations.
- Allowed methods: GET, POST, PUT, DELETE.
- Use path_params for path variables.
- POST and PUT request bodies must follow the endpoint schema.
- Include realistic positive and negative tests when justified.
- Use expected status codes documented in the specification.
- Do not include Markdown, explanations, Python code or extra keys.
- Never invent endpoints.
"""

    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        },
        timeout=60
    )
    response.raise_for_status()

    output = response.json().get("response", "")
    parsed = json.loads(output)

    if isinstance(parsed, dict):
        parsed = parsed.get("tests", [])

    if not isinstance(parsed, list):
        raise ValueError("Model output must contain a tests array")

    return parsed


def execute_case(case):
    path = case["endpoint"]
    for key, value in case.get("path_params", {}).items():
        path = path.replace("{" + str(key) + "}", str(value))
    if re.search(r"\{[^}]+\}", path) or not path.startswith("/") or "://" in path or ".." in path:
        return {"test_id":case.get("test_id"),"endpoint":case.get("endpoint"),"method":case.get("method"),
                "actual_status":None,"actual_response":None,"passed":False,"error":"Unsafe path or missing path parameter"}
    method = case["method"].upper()
    if method not in ALLOWED_METHODS:
        return {"test_id":case.get("test_id"),"actual_status":None,"passed":False,"error":"Method not allowed"}
    started = time.perf_counter()
    try:
        r = requests.request(method, BASE_URL + path, json=case.get("body") if method in {"POST","PUT"} else None,
                             timeout=TIMEOUT_SECONDS)
        duration = round(time.perf_counter()-started, 4)
        try:
            body = r.json()
        except ValueError:
            body = r.text[:1000] if r.text else None
        status_ok = r.status_code == int(case.get("expected_status", 200))
        fields = case.get("required_fields", [])
        fields_ok = all(f in body for f in fields) if fields and isinstance(body, dict) else not fields
        passed = bool(status_ok and fields_ok)
        return {"test_id":case.get("test_id"),"endpoint":case.get("endpoint"),"method":method,
                "actual_url":BASE_URL+path,"expected_status":case.get("expected_status"),
                "actual_status":r.status_code,"actual_response":body,"passed":passed,
                "error":None if passed else f"Expected status {case.get('expected_status')}, got {r.status_code}; required fields valid={fields_ok}",
                "duration_seconds":duration,"test_type":case.get("test_type","unspecified"),
                "source":case.get("source","llm_generated")}
    except requests.RequestException as exc:
        return {"test_id":case.get("test_id"),"endpoint":case.get("endpoint"),"method":method,
                "expected_status":case.get("expected_status"),"actual_status":None,"actual_response":None,
                "passed":False,"error":f"Request error: {exc}","duration_seconds":round(time.perf_counter()-started,4)}

def run_agent(spec, use_ollama=False, model="qwen2.5-coder:3b-instruct"):
    endpoints = parse_openapi(spec)
    cases = None
    mode = "deterministic fallback"
    if use_ollama:
        try:
            candidate = ollama_cases(endpoints, model)
            valid = [c for c in (candidate or []) if _safe_case(c, endpoints)]
            if valid:
                cases = valid[:4]
                mode = f"local Ollama model: {model}"
        except Exception:
            pass
    if not cases:
        cases = fallback_cases(endpoints)
    # Ensure every selected test matches a parsed endpoint and method, and obey budget.
    cases = [c for c in cases if _safe_case(c, endpoints)][:MAX_REQUESTS]
    results = [execute_case(c) for c in cases]
    decision = "No additional test selected; initial tests completed within the request budget."
    # Bounded feedback: only one follow-up, only if a valid-user GET passed and missing-ID coverage is absent.
    has_missing = any(c.get("path_params", {}).get("user_id") == 999 for c in cases)
    valid_get_passed = any(r.get("method") == "GET" and r.get("actual_status") == 200 and r.get("passed") for r in results)
    if valid_get_passed and not has_missing and len(results) < MAX_REQUESTS and ("/users/{user_id}", "GET") in {(e["path"],e["method"]) for e in endpoints}:
        follow = {"test_id":"TC-FU01","endpoint":"/users/{user_id}","method":"GET","path_params":{"user_id":999},
                  "expected_status":404,"required_fields":[],"body":None,"test_type":"feedback_follow_up","source":"agent_feedback_loop"}
        if _safe_case(follow, endpoints):
            results.append(execute_case(follow))
            decision = "A passing existing-user test was observed; missing-ID coverage was absent, so one bounded follow-up test was added."
    elif has_missing:
        decision = "A missing-ID negative test was already included; no duplicate follow-up was added."
    return {"project":"AI API Testing Agent","target":BASE_URL,"generation_mode":mode,
            "endpoints_found":endpoints,"test_cases":cases,"results":results,
            "summary":{"total":len(results),"passed":sum(bool(r.get("passed")) for r in results),
                       "failed":sum(not bool(r.get("passed")) for r in results)},
            "agent_feedback_decision":decision,
            "safety":{"target_fixed_to_localhost":True,"allowed_methods":sorted(ALLOWED_METHODS),
                      "max_requests":MAX_REQUESTS,"timeout_seconds":TIMEOUT_SECONDS}}
