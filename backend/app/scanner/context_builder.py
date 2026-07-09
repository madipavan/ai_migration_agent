from pathlib import Path


class ContextBuilder:

    def __init__(self, project_path: str):
        self.root = Path(project_path)

    def read_file(self, relative_path):

        path = self.root / relative_path

        if not path.exists():
            return None

        try:
            return {"path": relative_path, "content": path.read_text(encoding="utf-8")}

        except Exception as e:
            return {"path": relative_path, "error": str(e)}

    def build(self, analysis: dict):

        context = {"project_type": analysis["project_type"], "files": []}

        targets = []

        targets += analysis.get("entry_points", [])

        targets += analysis.get("dependency_files", [])

        targets += analysis.get("config_files", [])

        targets += analysis.get("migration_critical_files", [])

        for file in targets:

            data = self.read_file(file)

            if data:
                context["files"].append(data)

        return context

    def build_dependency(self, analysis: dict):

        context = {"project_type": analysis["project_type"], "files": []}

        targets = []

        targets += analysis.get("dependency_files", [])
        for file in targets:

            data = self.read_file(file)

            if data:
                context["files"].append(data)

        return context
