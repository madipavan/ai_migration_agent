class StabilityAnalyzerAgent:

    def __init__(self, llm):
        self.llm = llm

    def analyze(self, version_context):

        prompt = f"""
You are a software ecosystem stability analyzer.

Your responsibility is to decide whether a project migration is required.

Current project versions:

{version_context}


Analyze:

1. Is the framework version stable and supported?
2. Is the language/runtime version supported?
3. Are dependencies outdated, deprecated, or abandoned?
4. Are build tools still compatible?
5. Is migration actually necessary?


Rules:
- Do NOT modify code
- Do NOT create migration steps
- Do NOT assume migration is always required
- If project is already healthy, say migration_required false
- Recommend only stable production versions
- Avoid beta, alpha, preview versions


Return ONLY JSON:

{{
 "migration_required": true | false,

 "current_status": "",

 "recommended_target": {{
    "framework": {{
       "name":"",
       "version":""
    }},
    "language": {{
       "name":"",
       "version":""
    }}
 }},

 "issues":[
    {{
      "type":"",
      "name":"",
      "current":"",
      "issue":"",
      "severity":"low|medium|high"
    }}
 ],

 "reasoning":""
}}
"""

        return self.llm.invoke(prompt)
