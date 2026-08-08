"""
Streamlit web app for the Autonomous Software Engineering Agent.

Run with:
    export MISTRAL_API_KEY=sk-...
    streamlit run app.py
"""
import os
import streamlit as st

from graph import build_graph
from tools.file_tool import write_file

st.set_page_config(
    page_title="Autonomous Software Engineering Agent",
    page_icon="🛠️",
    layout="wide",
)

# ------------------------------------------------------------------ #
# Sidebar — configuration
# ------------------------------------------------------------------ #
with st.sidebar:
    st.title("🛠️ Agent Settings")

    api_key_input = st.text_input(
        "MISTRAL_API_KEY",
        type="password",
        value=os.environ.get("MISTRAL_API_KEY", ""),
        help="Required. Not stored anywhere beyond this session.",
    )
    if api_key_input:
        os.environ["MISTRAL_API_KEY"] = api_key_input

    model = st.text_input(
        "Model",
        value=os.environ.get("AGENT_MODEL", "claude-sonnet-4-5"),
    )
    os.environ["AGENT_MODEL"] = model

    max_iterations = st.slider(
        "Max Coder ↔ Tester retries on test failure", 0, 5, 2
    )

    save_to_disk = st.checkbox("Save output files to ./workspace", value=True)

    st.markdown("---")
    st.markdown(
        "**Pipeline:**\n\n"
        "1. 🗂️ Planner — breaks down the requirement\n"
        "2. 💻 Coder — writes the implementation\n"
        "3. 🔍 Reviewer — reviews & fixes issues\n"
        "4. 🧪 Tester — writes & runs unit tests\n"
        "5. 🔁 loops back to Coder on failure, up to the retry limit"
    )

# ------------------------------------------------------------------ #
# Main area
# ------------------------------------------------------------------ #
st.title("🤖 Autonomous Software Engineering Agent")
st.caption("Planner → Coder → Reviewer → Tester, with automatic self-correction.")

requirement = st.text_area(
    "Describe what you want built",
    placeholder="e.g. Write a function that validates whether a string is a valid IPv4 address",
    height=100,
)

run_clicked = st.button("🚀 Run Agent Pipeline", type="primary", use_container_width=False)

STAGE_LABELS = {
    "planner": "🗂️ Planner",
    "coder": "💻 Coder",
    "reviewer": "🔍 Reviewer",
    "tester": "🧪 Tester",
    "finalize": "✅ Finalizing",
}

if run_clicked:
    if not os.environ.get("MISTRAL_API_KEY"):
        st.error("Please provide a MISTRAL_API_KEY in the sidebar first.")
        st.stop()
    if not requirement.strip():
        st.error("Please describe what you want built.")
        st.stop()

    app = build_graph()
    initial_state = {"requirement": requirement, "max_iterations": max_iterations}

    progress_box = st.status("Starting pipeline…", expanded=True)
    final_state = None

    try:
        for step in app.stream(initial_state):
            for node_name, node_state in step.items():
                label = STAGE_LABELS.get(node_name, node_name)
                if node_name == "tester":
                    verdict = "✅ tests passed" if node_state.get("passed") else "❌ tests failed"
                    progress_box.write(f"{label} — iteration {node_state.get('iteration', 0)} — {verdict}")
                else:
                    progress_box.write(f"{label} — done")
                final_state = node_state
        progress_box.update(label="Pipeline complete", state="complete", expanded=False)
    except Exception as e:
        progress_box.update(label="Pipeline failed", state="error")
        st.exception(e)
        st.stop()

    if final_state is None:
        st.error("Pipeline produced no output.")
        st.stop()

    st.session_state["result"] = final_state

# ------------------------------------------------------------------ #
# Results
# ------------------------------------------------------------------ #
result = st.session_state.get("result")
if result:
    passed = result.get("passed")
    iteration = result.get("iteration", 0)
    if passed:
        st.success(f"Tests passed after {iteration} iteration(s).")
    else:
        st.warning(f"Tests still failing after {iteration} iteration(s) — showing best attempt.")

    tab_plan, tab_code, tab_review, tab_tests, tab_exec, tab_report = st.tabs(
        ["Plan", "Code", "Review", "Tests", "Execution Log", "Full Report"]
    )

    with tab_plan:
        st.markdown(result.get("plan", "_No plan generated._"))

    with tab_code:
        st.code(result.get("code", ""), language="python")

    with tab_review:
        st.markdown(result.get("review", "_No review generated._"))

    with tab_tests:
        st.code(result.get("tests", ""), language="python")

    with tab_exec:
        st.code(result.get("execution_result", ""), language="text")

    with tab_report:
        st.markdown(result.get("final_output", ""))

    st.markdown("---")
    filename = result.get("filename", "solution.py")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "⬇️ Download code",
            data=result.get("code", ""),
            file_name=filename,
            mime="text/x-python",
        )
    with col2:
        st.download_button(
            "⬇️ Download tests",
            data=result.get("tests", ""),
            file_name=f"test_{filename}",
            mime="text/x-python",
        )
    with col3:
        st.download_button(
            "⬇️ Download report",
            data=result.get("final_output", ""),
            file_name="REPORT.md",
            mime="text/markdown",
        )

    if save_to_disk:
        code_path = write_file(filename, result.get("code", ""))
        test_path = write_file(f"test_{filename}", result.get("tests", ""))
        report_path = write_file("REPORT.md", result.get("final_output", ""))
        st.caption(f"Saved to `{code_path}`, `{test_path}`, `{report_path}`")
else:
    st.info("Enter a requirement above and click **Run Agent Pipeline** to get started.")