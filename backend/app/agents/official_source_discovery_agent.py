from langchain_core.output_parsers import JsonOutputParser


class OfficialSourceDiscoveryAgent:

    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser()

    async def discover(
        self,
        framework: dict,
        package_manager: dict,
    ):

        prompt = f"""
You are a software package ecosystem expert.

Your task is to identify the OFFICIAL source for obtaining the latest stable version of a framework or package.

Framework

{framework}

Package Manager

{package_manager}


Rules

- Return ONLY official sources.
- Prefer official package registries.
- If no registry exists, use the official API.
- If no API exists, use the official documentation.
- Never return StackOverflow.
- Never return Reddit.
- Never return blogs.
- Never return GitHub issues.
- Never return AI-generated URLs.
- Never guess URLs.
- If you cannot determine an official source, return null values.


Return ONLY JSON.

{{
    "source_type":"registry | api | documentation | unknown",

    "url":"",

    "method":"GET",

    "response_type":"json | html",

    "version_path":"",

    "notes":""
}}

Examples

Example 1

Input

Framework:
{{
    "name":"Angular",
    "package":"@angular/core"
}}

Package Manager:
{{
    "name":"npm"
}}

Output

{{
    "source_type":"registry",
    "url":"https://registry.npmjs.org/@angular/core",
    "method":"GET",
    "response_type":"json",
    "version_path":"dist-tags.latest",
    "notes":""
}}

Example 2

Input

Framework:
{{
    "name":"FastAPI",
    "package":"fastapi"
}}

Package Manager:
{{
    "name":"pypi"
}}

Output

{{
    "source_type":"registry",
    "url":"https://pypi.org/pypi/fastapi/json",
    "method":"GET",
    "response_type":"json",
    "version_path":"info.version",
    "notes":""
}}

Example 3

Input

Framework:
{{
    "name":"UnknownFramework"
}}

Package Manager:
{{
    "name":"unknown"
}}

Output

{{
    "source_type":"unknown",
    "url":null,
    "method":null,
    "response_type":null,
    "version_path":null,
    "notes":"Official source could not be determined."
}}
"""

        response = await self.llm.ainvoke(prompt)

        return self.parser.parse(response.content)
