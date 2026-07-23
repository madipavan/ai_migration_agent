from pathlib import Path
from app.state import AgentState

_PRIORITY_NAMES = [
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "poetry.lock",
    "pyproject.toml",
    "pom.xml",
    "build.gradle",
    "pubspec.yaml",
]


def collect_dependency_files(state: AgentState) -> list[dict[str, str]]:
    repo_root = Path(state["repo_root"])
    analysis = state.get("repo_analysis") or {}
    declared = list(analysis.get("dependency_files") or [])

    # Fallback discovery if classifier missed them.
    if not declared:
        for name in _PRIORITY_NAMES:
            candidate = repo_root / name
            if candidate.exists():
                declared.append(name)

    # Keep stable priority order, then any remaining declared paths.
    ordered: list[str] = []
    lowered = {p.replace("\\", "/"): p for p in declared}
    for name in _PRIORITY_NAMES:
        for rel, original in list(lowered.items()):
            if rel.endswith(name) or Path(rel).name == name:
                ordered.append(original)
                lowered.pop(rel, None)
                break
    ordered.extend(lowered.values())

    files: list[dict[str, str]] = []
    for rel in ordered:
        path = repo_root / rel
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        files.append({"path": rel.replace("\\", "/"), "content": content})

    return files
