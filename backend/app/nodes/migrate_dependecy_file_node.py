from __future__ import annotations

import os
from pathlib import Path

from langchain_core.messages import AIMessage

from app.crews.dependency_migrate_crew import run_dependency_migrate_crew
from app.state import AgentState

# Prefer Flutter/Dart manifests first (current demo path), then Python.
_PRIORITY_NAMES = (
    "pubspec.yaml",
    "requirements.txt",
    "pyproject.toml",
)


def _collect_dependency_files(state: AgentState) -> list[dict[str, str]]:
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


def _write_files(repo_root: str, files: list[dict[str, str]], *, dry_run: bool) -> list[str]:
    written: list[str] = []
    root = Path(repo_root)
    for item in files:
        rel = item["path"]
        target = root / rel
        if dry_run:
            written.append(f"{rel} (dry-run, not written)")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item["content"], encoding="utf-8", newline="\n")
        written.append(rel)
    return written


def _build_diff_summary(
    originals: list[dict[str, str]],
    updated: list[dict[str, str]],
    *,
    plan: str,
    notes: str,
    approved: bool,
    written: list[str],
) -> str:
    original_map = {f["path"]: f["content"] for f in originals}
    sections: list[str] = [
        "Dependency migration completed." if approved else "Dependency migration finished with reviewer warnings.",
        "",
        f"Approved: {approved}",
        "",
        "Plan:",
        plan or "(no plan returned)",
        "",
        "Notes:",
        notes or "(none)",
        "",
        "Files:",
    ]

    for item in updated:
        path = item["path"]
        before = original_map.get(path, "")
        after = item["content"]
        sections.append(f"- {path}")
        sections.append("--- before ---")
        sections.append(before[:4000] + ("..." if len(before) > 4000 else ""))
        sections.append("--- after ---")
        sections.append(after[:4000] + ("..." if len(after) > 4000 else ""))
        sections.append("")

    sections.append("Write result:")
    for path in written:
        sections.append(f"- {path}")

    return "\n".join(sections)


def migrate_dependecy_file_node(state: AgentState):
    print("Starting dependency file migration (CrewAI)...")

    repo_root = state.get("repo_root")
    if not repo_root:
        return {
            "messages": [
                AIMessage(content="Cannot migrate: repo_root is missing from state.")
            ]
        }

    originals = _collect_dependency_files(state)
    if not originals:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Migration approved, but no dependency files were found "
                        "(looked for pubspec.yaml, requirements.txt, pyproject.toml)."
                    )
                )
            ]
        }

    dry_run = os.getenv("MIGRATE_DRY_RUN", "").lower() in {"1", "true", "yes"}

    try:
        result = run_dependency_migrate_crew(
            framework=state.get("framework") or {},
            language=state.get("language") or {},
            latest_versions=state.get("latest_versions") or {},
            dependencies=state.get("repo_dependencies") or {},
            assessment=state.get("compatibility_assessment") or {},
            files=originals,
        )
    except Exception as exc:
        print(f"CrewAI migrate failed: {exc}")
        return {
            "messages": [
                AIMessage(
                    content=f"Dependency migration failed while running CrewAI crew:\n{exc}"
                )
            ]
        }

    written = _write_files(repo_root, result["files"], dry_run=dry_run)
    summary = _build_diff_summary(
        originals,
        result["files"],
        plan=result.get("plan", ""),
        notes=result.get("notes", ""),
        approved=bool(result.get("approved", True)),
        written=written,
    )

    print("Dependency file migration finished.")
    return {
        "messages": [AIMessage(content=summary)],
        "pending_action": None,
    }
