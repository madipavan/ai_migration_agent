from langchain_core.output_parsers import JsonOutputParser


class CompatibilityAssessmentAgent:

    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser()

    async def assess(
        self,
        framework,
        language,
        runtime,
        package_manager,
        build_tools,
        latest_versions,
        dependencies,
    ):

        prompt = f"""
You are a senior software migration architect.

Your job is to assess whether a project requires a migration or whether updating dependencies is sufficient.

Current Project

Framework
{framework}

Language
{language}

Runtime
{runtime}

Package Manager
{package_manager}

Build Tools
{build_tools}

Dependencies
{dependencies}

Latest Stable Versions
{latest_versions}


Rules

- Think carefully.
- Do NOT create a migration plan.
- Do NOT suggest commands.
- Do NOT modify code.
- Only assess compatibility.
- Determine if runtime upgrades are required.
- Determine whether dependency updates alone are sufficient.
- Determine whether breaking changes are expected.

Return ONLY JSON FOR EXAMPLE.

{{
    "migration_required": true,

    "update_only": false,

    "severity": "major",

    "breaking_changes": true,

    "runtime_upgrade_required": true,

    "build_tool_upgrade_required": true,

    "dependency_updates_required": true,

    "estimated_complexity": "medium",

    "summary": ""
}}
"""

        response = await self.llm.ainvoke(prompt)

        return self.parser.parse(response.content)
