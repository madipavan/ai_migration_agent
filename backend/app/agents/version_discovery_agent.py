class VersionDiscoveryAgent:

    def __init__(self, llm):
        self.llm = llm

    def discover(self, repo_context):

        prompt = f"""
You are a software version discovery engine.

Your job is ONLY to discover the current technology versions.

Repository context:

{repo_context}


Extract:

1. Primary framework and version
2. Programming language and version
3. Runtime versions
4. Build tools versions
5. Package manager
6. Dependencies and their current versions


Rules:
- Do NOT suggest upgrades
- Do NOT create migration plans
- Do NOT guess missing versions
- If unknown, return null
- Use only provided files


Return ONLY JSON:

{{
  "framework": {{
      "name":"",
      "package": "",
      "version":""
  }},

  "language": {{
      "name":"",
      "version":""
  }},

  "runtime": {{
      "name":"",
      "version":""
  }},

  "package_manager": {{
      "name":"",
      "version":""
  }},

  "build_tools":[
      {{
        "name":"",
        "version":""
      }}
  ],

  "dependencies":[
      {{
        "name":"",
        "version":""
      }}
  ]
}}
"""

        return self.llm.invoke(prompt)
