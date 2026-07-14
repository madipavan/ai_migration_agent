from app.models.file_classification_model import FileClassificationModel


class FileClassifierAgent:

    def __init__(self, llm):
        self.llm = llm.with_structured_output(FileClassificationModel)

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
- Exclude files that can be recreated automatically.
"""

        result = self.llm.invoke(prompt)

        return result
