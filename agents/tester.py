import os
try:
    from ..state import AgentState
except ImportError:
    from state import AgentState
from agents.llm_client import call_llm, extract_code_block
from tools.code_executor import run_code_and_tests

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "tester.txt")


def _load_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def tester_node(state: AgentState) -> AgentState:
    """Generate a unit test suite for the code, then execute code + tests safely."""
    prompt = _load_prompt().format(
        requirement=state["requirement"],
        code=state.get("code", ""),
    )
    response = call_llm(prompt, system="You are the Tester agent. Output only test code.")
    test_code = extract_code_block(response)

    result = run_code_and_tests(state.get("code", ""), test_code)

    execution_summary = (
        f"Return code: {result.returncode}\n"
        f"--- STDOUT ---\n{result.stdout}\n"
        f"--- STDERR ---\n{result.stderr}\n"
    )
    if result.timed_out:
        execution_summary += "\n[WARNING] Execution timed out.\n"

    iteration = state.get("iteration", 0) + 1

    return {
        **state,
        "tests": test_code,
        "execution_result": execution_summary,
        "passed": result.success,
        "iteration": iteration,
    }
