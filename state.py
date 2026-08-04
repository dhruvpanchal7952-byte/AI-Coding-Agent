"""
Shared state schema for the Autonomous Software Engineering Agent graph.
Every node (Planner, Coder, Reviewer, Tester) reads from and writes to this state.
"""
from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    requirement: str         
    plan: str                 
    code: str                
    review: str               
    tests: str                
    execution_result: str     
    final_output: str         
    iteration: int             
    max_iterations: int        
    passed: bool                
    filename: str               
