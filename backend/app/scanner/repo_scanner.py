from pathlib import Path

IGNORE_DIR = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
}


class RepoScanner:

    def __init__(self, project_path: str):
        self.root = Path(project_path)

    def should_ignore(self, path: Path):
        return any(part in IGNORE_DIR for part in path.parts)

    def scan(self):

        files = []

        for path in self.root.rglob("*"):

            if self.should_ignore(path):
                continue

            if path.is_file():

                files.append(
                    {
                        "name": path.name,
                        "relative_path": str(path.relative_to(self.root)),
                        "extension": path.suffix,
                        "size": path.stat().st_size,
                    }
                )

        return files
