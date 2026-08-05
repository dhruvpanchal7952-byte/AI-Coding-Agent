"""
Executes Python code / test files in a subprocess with:
  - a hard timeout
  - a dedicated temp working directory (auto-cleaned)
  - no network access assumptions (caller's OS/network policy still applies)
  - captured stdout/stderr

This is a *process-level* sandbox (isolates crashes, infinite loops, filesystem
side effects to a temp dir). It is NOT a full security sandbox against a
malicious actor with intent to escape the OS — do not use this to run
untrusted third-party code without an additional container/VM layer.
"""
import subprocess
import sys
import tempfile
import os
import shutil
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False


def run_python_file(filepath: str, timeout: int = 15) -> ExecutionResult:
    """Run a standalone python file and capture the result."""
    try:
        proc = subprocess.run(
            [sys.executable, filepath],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecutionResult(
            success=proc.returncode == 0,
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )
    except subprocess.TimeoutExpired as e:
        return ExecutionResult(
            success=False,
            stdout=e.stdout or "",
            stderr=(e.stderr or "") + "\n[Execution timed out]",
            returncode=-1,
            timed_out=True,
        )


def run_code_and_tests(solution_code: str, test_code: str, timeout: int = 20) -> ExecutionResult:
    """
    Write solution.py and test_solution.py into a fresh temp dir, then
    run `python -m unittest test_solution` from inside that dir.
    """
    tmpdir = tempfile.mkdtemp(prefix="agent_exec_")
    try:
        sol_path = os.path.join(tmpdir, "solution.py")
        test_path = os.path.join(tmpdir, "test_solution.py")

        with open(sol_path, "w", encoding="utf-8") as f:
            f.write(solution_code)
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "test_solution", "-v"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return ExecutionResult(
                success=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
            )
        except subprocess.TimeoutExpired as e:
            return ExecutionResult(
                success=False,
                stdout=e.stdout or "",
                stderr=(e.stderr or "") + "\n[Execution timed out]",
                returncode=-1,
                timed_out=True,
            )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
