import os
try:
    from ..state import AgentState
except ImportError:
    from state import AgentState
from agents.llm_client import call_llm, extract_code_block

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "reviewer.txt")


def _load_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

def reviewer_node(state: AgentState) -> AgentState:
    """Critically review the generated code and return an improved version."""
    prompt = _load_prompt().format(
        requirement=state["requirement"],
        plan=state.get("plan", ""),
        code=state.get("code", ""),
    )
    response = call_llm(prompt, system="You are the Reviewer agent. Be thorough but fair.")
    fixed_code = extract_code_block(response)

    return {**state, "review": response, "code": fixed_code}
