import os
import re

from agents.llm_client import call_llm
import os
import sys

#This is for run this file 
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


from state import AgentState

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "planner.txt")

def _load_prompt() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

def planner_node(state: AgentState) -> AgentState:
    """Break the user's requirement into an implementation plan."""
    prompt = _load_prompt().format(requirement=state["requirement"])
    response = call_llm(prompt, system="You are the Planner agent. Be concise and structured.")

    filename_match = re.search(r"FILENAME:\s*(\S+)", response)
    filename = filename_match.group(1).strip() if filename_match else "solution.py"

    return {
        **state,
        "plan": response,
        "filename": filename,
        "iteration": 0,
        "max_iterations": state.get("max_iterations", 2),
    }