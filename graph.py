"""
Builds the LangGraph StateGraph:

    START -> Planner -> Coder -> Reviewer -> Tester -> [conditional] -> END
                              ^                            |
                              |____________________________|
                          (loop back to Coder if tests fail
                           and max_iterations not yet reached)
"""
from langgraph.graph import StateGraph, END

from state import AgentState
from agents.planner import planner_node
from agents.coder import coder_node
from agents.reviewer import reviewer_node
from agents.tester import tester_node


def _route_after_tester(state: AgentState) -> str:
    if state.get("passed"):
        return "finalize"
    if state.get("iteration", 0) >= state.get("max_iterations", 2):
        return "finalize"  
    return "retry"


def _finalize_node(state: AgentState) -> AgentState:
    status = "PASSED" if state.get("passed") else "FAILED (max iterations reached)"
    final_output = (
        f"# Autonomous Software Engineering Agent — Result\n\n"
        f"**Requirement:** {state['requirement']}\n\n"
        f"**Status:** {status} after {state.get('iteration', 0)} iteration(s)\n\n"
        f"## Plan\n{state.get('plan', '')}\n\n"
        f"## Final Code (`{state.get('filename', 'solution.py')}`)\n"
        f"```python\n{state.get('code', '')}\n```\n\n"
        f"## Review Notes\n{state.get('review', '')}\n\n"
        f"## Tests\n```python\n{state.get('tests', '')}\n```\n\n"
        f"## Execution Result\n```\n{state.get('execution_result', '')}\n```\n"
    )
    return {**state, "final_output": final_output}


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("coder", coder_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("tester", tester_node)
    graph.add_node("finalize", _finalize_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "reviewer")
    graph.add_edge("reviewer", "tester")

    graph.add_conditional_edges(
        "tester",
        _route_after_tester,
        {"retry": "coder", "finalize": "finalize"},
    )
    graph.add_edge("finalize", END)

    return graph.compile()
