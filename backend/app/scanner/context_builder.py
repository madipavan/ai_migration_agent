from pathlib import Path


class ContextBuilder:

    def __init__(self, analysis: dict):
        self.analysis = analysis

    def read_file(self, relative_path):

        path = self.root / relative_path

        if not path.exists():
            return None

        try:
            return {"path": relative_path, "content": path.read_text(encoding="utf-8")}

        except Exception as e:
            return {"path": relative_path, "error": str(e)}

    def build(self):

        context = {"project_type": self.analysis["project_type"], "files": []}

        targets = []

        targets += self.analysis.get("entry_points", [])

        targets += self.analysis.get("dependency_files", [])

        targets += self.analysis.get("config_files", [])

        targets += self.analysis.get("migration_critical_files", [])

        for file in targets:

            data = self.read_file(file)

            if data:
                context["files"].append(data)

        return context

    def build_dependency(self):

        context = {"project_type": self.analysis["project_type"], "files": []}

        targets = []

        targets += self.analysis.get("dependency_files", [])
        for file in targets:

            data = self.read_file(file)

            if data:
                context["files"].append(data)

        return context
