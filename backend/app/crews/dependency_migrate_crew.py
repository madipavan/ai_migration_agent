"""CrewAI crew that plans and rewrites dependency manifest files."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task


def _get_crew_llm() -> LLM:
    api_key = os.getenv("MISTRAL") or os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MISTRAL (or MISTRAL_API_KEY) env var is required for CrewAI migrate."
        )

    # Use Mistral's OpenAI-compatible endpoint. The litellm `mistral/` route
    # currently breaks with CrewAI message metadata (cache_breakpoint).
    return LLM(
        model="mistral-small-latest",
        api_key=api_key,
        base_url="https://api.mistral.ai/v1",
        temperature=0.2,
    )


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("Crew returned empty output.")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError(f"Could not parse JSON from crew output:\n{text[:800]}")


def run_dependency_migrate_crew(
    *,
    framework: dict,
    language: dict,
    latest_versions: dict,
    dependencies: dict | list,
    assessment: dict,
    files: list[dict[str, str]],
) -> dict[str, Any]:
    """
    Run Planner → Migrator → Reviewer and return:
    {
      "plan": str,
      "files": [{"path": str, "content": str}],
      "notes": str,
      "approved": bool
    }
    """
    llm = _get_crew_llm()

    file_blocks = "\n\n".join(
        f"### FILE: {item['path']}\n```\n{item['content']}\n```" for item in files
    )

    context_blob = f"""
Framework: {json.dumps(framework, default=str)}
Language: {json.dumps(language, default=str)}
Latest versions: {json.dumps(latest_versions, default=str)}
Current dependencies: {json.dumps(dependencies, default=str)}
Compatibility assessment: {json.dumps(assessment, default=str)}

Dependency files to migrate:
{file_blocks}
"""

    planner = Agent(
        role="Dependency Migration Planner",
        goal="Produce a safe, ordered dependency upgrade plan from the assessment.",
        backstory=(
            "You are a senior release engineer. You prioritize SDK/runtime constraints first, "
            "then framework packages, then app dependencies. You never invent packages."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    migrator = Agent(
        role="Dependency File Migrator",
        goal="Rewrite dependency manifest files according to the approved plan.",
        backstory=(
            "You specialize in pubspec.yaml, requirements.txt, and pyproject.toml. "
            "You preserve unrelated keys, comments where possible, and valid file syntax."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    reviewer = Agent(
        role="Dependency Migration Reviewer",
        goal="Validate migrated manifests and return final approved JSON only.",
        backstory=(
            "You catch unsafe major bumps, invalid YAML/TOML/requirements syntax, "
            "and missing SDK constraints. You output strict JSON for machines."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    plan_task = Task(
        description=f"""
Using this project context, write a concise migration plan for updating dependency files only
(do not rewrite application source code).

Context:
{context_blob}

Return a numbered plan covering:
1) runtime/SDK constraint updates
2) framework/language bumps
3) package dependency bumps
4) risks / breaking-change notes
""",
        expected_output="A clear numbered migration plan in plain text.",
        agent=planner,
    )

    migrate_task = Task(
        description=f"""
Apply the planner's plan and produce updated full file contents for each dependency file.

Rules:
- Output complete file contents, not patches.
- Keep valid syntax for pubspec.yaml / requirements.txt / pyproject.toml.
- Prefer latest_versions and assessment guidance; do not invent unknown packages.
- Preserve project name, description, and unrelated config sections.

Original files:
{file_blocks}
""",
        expected_output="Updated file contents for each path, clearly labeled.",
        agent=migrator,
        context=[plan_task],
    )

    review_task = Task(
        description="""
Review the plan and migrated files. Return ONLY valid JSON (no markdown outside JSON) with this schema:

{
  "approved": true,
  "plan": "short plan summary",
  "notes": "reviewer notes / risks",
  "files": [
    {"path": "pubspec.yaml", "content": "full file content here"}
  ]
}

If something is unsafe, still return best-effort corrected files with approved=false and explain in notes.
Paths must match the original relative paths.
""",
        expected_output="Strict JSON object with approved, plan, notes, and files array.",
        agent=reviewer,
        context=[plan_task, migrate_task],
    )

    crew = Crew(
        agents=[planner, migrator, reviewer],
        tasks=[plan_task, migrate_task, review_task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    raw = (
        str(result.raw)
        if hasattr(result, "raw") and result.raw is not None
        else str(result)
    )
    parsed = _extract_json(raw)

    files_out = parsed.get("files") or []
    if not isinstance(files_out, list) or not files_out:
        raise ValueError("Crew JSON missing non-empty 'files' array.")

    normalized_files: list[dict[str, str]] = []
    for item in files_out:
        path = (item or {}).get("path")
        content = (item or {}).get("content")
        if not path or content is None:
            continue
        normalized_files.append(
            {"path": str(path).replace("\\", "/"), "content": str(content)}
        )

    if not normalized_files:
        raise ValueError("Crew JSON files entries were invalid.")

    return {
        "approved": bool(parsed.get("approved", True)),
        "plan": str(parsed.get("plan") or ""),
        "notes": str(parsed.get("notes") or ""),
        "files": normalized_files,
        "raw": raw,
    }
