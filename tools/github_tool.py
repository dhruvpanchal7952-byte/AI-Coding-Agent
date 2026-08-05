"""
Minimal git integration: init a repo, commit generated code, optionally push.
Uses the `git` CLI via subprocess rather than a GitHub API client, so it works
for any remote (GitHub, GitLab, etc.) that the local git config already trusts.

Pushing requires the local environment to already have credentials configured
(SSH key or a credential helper / PAT). This module never stores or logs secrets.
"""
import subprocess
from dataclasses import dataclass


@dataclass
class GitResult:
    success: bool
    output: str


def _run(args: list[str], cwd: str) -> GitResult:
    try:
        proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30)
        ok = proc.returncode == 0
        return GitResult(success=ok, output=(proc.stdout + proc.stderr).strip())
    except FileNotFoundError:
        return GitResult(success=False, output="git is not installed or not on PATH.")
    except subprocess.TimeoutExpired:
        return GitResult(success=False, output="git command timed out.")


def init_repo(path: str) -> GitResult:
    return _run(["git", "init"], cwd=path)


def commit_all(path: str, message: str) -> GitResult:
    add_res = _run(["git", "add", "-A"], cwd=path)
    if not add_res.success:
        return add_res
    return _run(["git", "commit", "-m", message], cwd=path)


def create_branch(path: str, branch_name: str) -> GitResult:
    return _run(["git", "checkout", "-b", branch_name], cwd=path)


def push(path: str, remote: str = "origin", branch: str = "main") -> GitResult:
    return _run(["git", "push", remote, branch], cwd=path)


def status(path: str) -> GitResult:
    return _run(["git", "status", "--short"], cwd=path)
