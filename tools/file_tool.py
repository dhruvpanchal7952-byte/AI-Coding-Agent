"""
Simple, safe file I/O helpers scoped to a working directory (default: ./workspace).
Prevents path traversal outside the workspace root.
"""
import os

DEFAULT_WORKSPACE = os.path.join(os.getcwd(), "workspace")


def _resolve(path: str, workspace: str = DEFAULT_WORKSPACE) -> str:
    os.makedirs(workspace, exist_ok=True)
    full = os.path.normpath(os.path.join(workspace, path))
    if not full.startswith(os.path.normpath(workspace)):
        raise ValueError(f"Refusing to write outside workspace: {path}")
    return full


def write_file(path: str, content: str, workspace: str = DEFAULT_WORKSPACE) -> str:
    """Write content to a file inside the workspace. Returns the full path written."""
    full = _resolve(path, workspace)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return full


def read_file(path: str, workspace: str = DEFAULT_WORKSPACE) -> str:
    """Read and return the content of a file inside the workspace."""
    full = _resolve(path, workspace)
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def list_files(workspace: str = DEFAULT_WORKSPACE) -> list[str]:
    os.makedirs(workspace, exist_ok=True)
    out = []
    for root, _, files in os.walk(workspace):
        for name in files:
            out.append(os.path.relpath(os.path.join(root, name), workspace))
    return out
