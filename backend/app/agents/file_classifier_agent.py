class FileClassifierAgent:

    def __init__(self, llm):
        self.llm = llm

    def classify(self, files):

        prompt = f"""
You are a senior software migration engineer.

You are analyzing a repository for a migration task.

You ONLY have the file tree and metadata.

Files:
{files}


Your task:

Find files required to understand and migrate this project.

Rules:
- Include files developers actually edit
- Include entry points
- Include dependency/config/build files
- Include architecture files
- Exclude generated files
- Exclude caches
- Exclude build outputs
- Exclude IDE files
- Exclude files that can be recreated automatically

Return ONLY valid JSON:

{{
  "project_type": "",
  "entry_points": [],
  "dependency_files": [],
  "config_files": [],
  "migration_critical_files": [],
  "source_directories": [],
  "ignored_files": []
}}
"""

        return self.llm.invoke(prompt)
