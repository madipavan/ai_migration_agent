from app.scanner.repo_scanner import scan_files, get_file_metadata
from pathlib import Path

files = scan_files(proj_path="D:/migration_ai_agent/backend")


dict = get_file_metadata(path=Path(files[3]))

