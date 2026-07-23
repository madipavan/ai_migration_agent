"""CrewAI crew that plans and rewrites dependency manifest files."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task

from app.crew_tools.latest_version_tool import LatestVersionTool
from app.services.latest_version.latest_version_service import LatestVersionService


def _get_crew_llm() -> LLM:
    api_key = os.getenv("MISTRAL") or os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MISTRAL (or MISTRAL_API_KEY) env var is required for CrewAI migrate."
        )

    # Use Mistral's OpenAI-compatible endpoint. The litellm `mistral/` route
    # currently breaks with CrewAI message metadata (cache_breakpoint).
    return LLM(
        model="mistral-medium",
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
    package_manager: dict,
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

    latest_version_tool = LatestVersionTool(
        service=LatestVersionService(llm=llm),
        framework=framework,
        package_manager=package_manager,
    )
    planner = Agent(
        role="Dependency Migration Planner",
        goal="""Produce a safe dependency migration plan and identify every dependency that is:
          - Kept
          - Upgraded
          - Downgraded
          - Replaced
          - Deprecated
          - Removed

            For every dependency that is not kept, provide:
            - old package
            - new package (if any)
            - reason
            - expected import path changes (if known)""",
        backstory=(
            "You are a senior release engineer. You prioritize SDK/runtime constraints first, "
            "then framework packages, then app dependencies. You never invent packages."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        tools=[latest_version_tool],
    )

    migrator = Agent(
        role="Dependency File Migrator",
        goal="Rewrite dependency manifest files according to the approved plan.",
        backstory=(
            "You specialize in migrating any pacakage file for example pubspec.yaml, requirements.txt, and pyproject.toml. "
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
Using the project context, create a dependency migration plan only.
Do NOT rewrite application source code.

Context:
{context_blob}

CRITICAL RULES

- latest_versions contains ONLY the target framework, language and runtime versions.
- It DOES NOT contain dependency package versions.
- For every dependency that requires a version lookup, you MUST use the latest_version_tool.
- Never use your own knowledge or memory for dependency versions.
- Never guess dependency versions.
- If the LatestVersionTool cannot determine a version:
    - Keep the current version.
    - Mention the package in the migration risks.
- Use the compatibility assessment when deciding whether a dependency should be kept, upgraded, replaced, removed, or deprecated.
- Prioritize runtime and framework compatibility before upgrading dependencies.
- Only recommend officially supported replacement packages.

For every dependency that is not KEEP include:

- package name
- current version
- target version (if available)
- replacement package (if applicable)
- reason
- migration risk
- expected import changes (if known)

Return a numbered migration plan covering:

1. Runtime / SDK updates
2. Framework updates
3. Dependency changes
4. Deprecated or replaced packages
5. Potential breaking changes
6. Migration risks
7. Validation steps after migration
""",
        expected_output="A clear numbered migration plan in plain text.",
        agent=planner,
    )

    migrate_task = Task(
        description=f"""
Apply the planner's migration plan and generate the updated dependency manifest(s).

CRITICAL RULES

- Output COMPLETE file contents. Never output patches.
- Preserve valid syntax for every dependency manifest.
- Preserve formatting and unrelated configuration.
- Never invent package names.
- Never invent package versions.
- Use ONLY versions available in latest_versions.
- If a package is missing from latest_versions:
    - Keep the existing version.
    - Mention it in the migration notes.
- Update SDK/runtime constraints before dependency upgrades.
- Upgrade packages according to latest_versions and compatibility assessment.
- Replace deprecated packages with their recommended replacements.
- Remove deprecated packages from the final manifest.
- Preserve project metadata (name, description, scripts, plugins, etc.).
- Generate a dependency_changes report describing every dependency decision.
- The generated dependency manifest must be ready to execute with the package manager without requiring manual edits.

Original files:

{file_blocks}
""",
        expected_output="""
Updated dependency manifests together with a complete dependency_changes report.
""",
        agent=migrator,
        context=[plan_task],
    )
    review_task = Task(
        description="""
Review the migrated dependency manifests.

Verify all of the following:

- Dependency manifests are syntactically valid.
- SDK/runtime constraints are compatible.
- Every original dependency has exactly one migration decision.
- No dependency has been silently removed.
- dependency_changes completely describes every dependency.
- Package versions match latest_versions.
- No package version has been invented.
- Replacement packages are compatible with the target framework.

If build or package manager output is provided (for example:
flutter pub get,
dart pub get,
npm install,
pnpm install,
yarn install,
pip install,
dotnet restore,
cargo check,
gradle build),

analyze the errors and automatically fix the dependency manifests whenever possible.

If a conflict can be resolved safely,
return the corrected dependency files.

If the error cannot be resolved automatically,
set approved=false and clearly explain the blocking issue.

Return ONLY valid JSON.

Schema:

{
  "approved": true,
  "plan": "...",
  "notes": "...",
  "files": [
    {
      "path": "...",
      "content": "..."
    }
  ],
  "dependency_changes": [
    {
      "package": "...",
      "action": "keep|upgrade|replace|remove|deprecated",
      "replacement": null,
      "reason": "...",
      "imports": []
    }
  ]
}

Paths must match the original relative paths.
Never return Markdown.
Never return explanations outside JSON.
""",
        expected_output="""
Strict JSON containing approved, plan, notes, files and dependency_changes.
""",
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
        "dependency_changes": parsed.get("dependency_changes", []),
        "raw": raw,
    }
