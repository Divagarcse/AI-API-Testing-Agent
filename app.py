import json
import streamlit as st
from agent_core import run_agent

st.set_page_config(page_title="AI API Testing Agent", page_icon="🧪", layout="wide")
st.title("AI API Testing Agent")
st.caption("From OpenAPI specification to automated test reports — local-first MVP")
st.info("Safety: requests are sent only to the fixed local demo API at 127.0.0.1:8000. POST/PUT/DELETE modify only the included in-memory demo data. Start the API server in a separate terminal first.")

uploaded = st.file_uploader("Upload an OpenAPI JSON specification", type=["json"])
default_model = "qwen2.5-coder:3b-instruct"
use_ollama = st.checkbox("Try local Ollama model (optional; deterministic tests run if unavailable)", value=False)
model = st.text_input("Installed Ollama model name", value=default_model, disabled=not use_ollama)

if uploaded is not None:
    try:
        spec = json.load(uploaded)
        st.subheader("Specification preview")
        st.json({"title":spec.get("info",{}).get("title"),"openapi":spec.get("openapi"),"paths":list(spec.get("paths",{}).keys())})
        if st.button("Run agent tests", type="primary"):
            with st.spinner("Generating, validating, executing, and analyzing tests..."):
                st.session_state["report"] = run_agent(spec, use_ollama=use_ollama, model=model.strip() or default_model)
    except Exception as e:
        st.error(f"Could not read this JSON file: {e}")

report = st.session_state.get("report")
if report:
    st.divider()
    st.subheader("Test summary")
    c1,c2,c3 = st.columns(3)
    c1.metric("Total", report["summary"]["total"])
    c2.metric("Passed", report["summary"]["passed"])
    c3.metric("Failed", report["summary"]["failed"])
    st.write("**Test generation mode:**", report["generation_mode"])
    st.write("**Agent feedback decision:**", report["agent_feedback_decision"])
    st.subheader("Execution results")
    st.dataframe([{"Test ID":r.get("test_id"),"Method":r.get("method"),"Endpoint":r.get("endpoint"),
                   "Expected":r.get("expected_status"),"Actual":r.get("actual_status"),
                   "Result":"PASS" if r.get("passed") else "FAIL","Duration (s)":r.get("duration_seconds"),
                   "Source":r.get("source"),"Error":r.get("error")} for r in report["results"]], use_container_width=True)
    for r in report["results"]:
        with st.expander(f'{r.get("test_id")} — {"PASS" if r.get("passed") else "FAIL"}'):
            st.json(r)
    st.download_button("Download JSON report", data=json.dumps(report, indent=2),
                       file_name="ai_api_test_report.json", mime="application/json")
    st.caption("The included tests use a controlled local demo API. Ollama is optional; if not used, report generation mode will say deterministic fallback.")
