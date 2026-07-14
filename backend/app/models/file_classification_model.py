from pydantic import BaseModel


class FileClassificationModel(BaseModel):
    project_type: str
    entry_points: list[str]
    dependency_files: list[str]
    config_files: list[str]
    migration_critical_files: list[str]
    source_directories: list[str]
    ignored_files: list[str]
