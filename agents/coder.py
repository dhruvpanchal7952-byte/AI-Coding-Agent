import os
try:
    from ..state import AgentState
except ImportError:
    from state import AgentState
from agents.llm_client import call_llm, extract_code_block

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "coder.txt")


def _load_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def coder_node(state: AgentState) -> AgentState:
    """Generate (or regenerate, on a revision loop) code implementing the plan."""
    revision_context = ""
    if state.get("execution_result") and not state.get("passed", True):
        revision_context = (
            "NOTE: A previous version of this code FAILED when executed/tested. "
            "Fix the following issue(s) in your new version:\n"
            f"{state['execution_result']}\n"
        )
    elif state.get("review"):
        revision_context = (
            "NOTE: Incorporate the reviewer's fixed code below as your starting point, "
            "unless you spot further issues:\n"
            f"{state['review']}\n"
        )

    prompt = _load_prompt().format(
        requirement=state["requirement"],
        plan=state.get("plan", ""),
        revision_context=revision_context,
    )
    response = call_llm(prompt, system="You are the Coder agent. Output only code.")
    code = extract_code_block(response)

    return {**state, "code": code}
