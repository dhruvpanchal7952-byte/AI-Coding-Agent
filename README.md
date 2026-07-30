# AI Coding Agent

A multi-agent system (built on [LangGraph](https://github.com/langchain-ai/langgraph) +
the Anthropic API) that turns a natural-language requirement into working, tested Python
code — end to end, with no human in the loop unless the self-correction budget runs out.

## Architecture

```
User Requirement
      │
      ▼
┌────────────────┐
│ Planner Agent   │  Breaks the requirement into a concrete implementation plan
└────────────────┘
      │
      ▼
┌────────────────┐
│ Coder Agent     │  Generates code implementing the plan
└────────────────┘
      │
      ▼
┌────────────────┐
│ Reviewer Agent  │  Reviews code quality/correctness/security, returns fixed code
└────────────────┘
      │
      ▼
┌────────────────┐
│ Tester Agent    │  Writes unit tests, executes code+tests in a sandboxed subprocess
└────────────────┘
      │
      ├─ tests fail & retries left ──► back to Coder Agent (with failure context)
      │
      ▼ tests pass, or retry budget exhausted
  Final Output (code + tests + review notes + execution log)
```

## Project Structure

```
ai-coding-agent/
├── agents/
│   ├── llm_client.py    # shared Anthropic API wrapper
│   ├── planner.py
│   ├── coder.py
│   ├── reviewer.py
│   └── tester.py
├── tools/
│   ├── github_tool.py   # git init/commit/branch/push helpers
│   ├── code_executor.py # sandboxed subprocess execution with timeout
│   ├── file_tool.py     # workspace-scoped read/write helpers
│   └── search_tool.py   # DuckDuckGo-backed web search
├── prompts/
│   ├── planner.txt
│   ├── coder.txt
│   ├── reviewer.txt
│   └── tester.txt
├── graph.py              # LangGraph StateGraph wiring + retry logic
├── state.py               # AgentState TypedDict schema
├── main.py                # CLI entry point
├── app.py                 # Streamlit web UI entry point
├── requirements.txt
└── README.md
```

## Setup

```bash
cd ai-coding-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...       # required
export AGENT_MODEL=claude-sonnet-4-5       # optional, defaults to claude-sonnet-4-5
```

## Usage

### Web UI (Streamlit)

```bash
streamlit run app.py
```

Opens a browser UI where you can enter the API key (or set `ANTHROPIC_API_KEY` beforehand),
type a requirement, watch each agent's progress live, browse the Plan/Code/Review/Tests/
Execution Log in tabs, and download the generated files.

### CLI

```bash
python main.py "Write a function that checks if a number is prime"

# Allow more self-correction attempts if tests fail
python main.py --max-iterations 3 "Build a simple LRU cache class"

# Don't persist output files, just print the report
python main.py --no-save "Implement binary search"
```

On success, three files are written to `./workspace/`:
- `<name>.py` — the final reviewed code
- `test_<name>.py` — the generated unit test suite
- `REPORT.md` — the full run report (plan, review notes, execution log)

## How self-correction works

The Tester agent runs the Coder/Reviewer's code against a freshly generated unit test
suite inside an isolated subprocess with a timeout (`tools/code_executor.py`). If the
run fails, the failure output (stdout/stderr/traceback) is fed back into the **Coder**
agent as context on the next loop iteration, and the Coder/Reviewer/Tester sequence
repeats — up to `max_iterations` times (default 2) — before the graph gives up and
reports the failure transparently rather than looping forever.

## Notes on the code executor sandbox

`tools/code_executor.py` isolates execution to a temp directory and enforces a wall-clock
timeout, which contains crashes, infinite loops, and filesystem side effects. It is a
**process-level** sandbox, not a security boundary against a deliberately malicious actor —
for running fully untrusted third-party code, put this behind an additional container or VM.

## Extending

- **Git integration**: `tools/github_tool.py` exposes `init_repo`, `commit_all`,
  `create_branch`, and `push`. Wire a git-commit step into `graph.py` after `finalize`
  if you want every successful run auto-committed.
- **Different LLM/provider**: swap the implementation in `agents/llm_client.py`.
- **Different search backend**: swap the implementation in `tools/search_tool.py`
  (e.g. Tavily, Bing, or Anthropic's built-in web_search tool).
