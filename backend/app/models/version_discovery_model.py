from pydantic import BaseModel


class VersionInfoModel(BaseModel):
    name: str | None = None
    version: str | None = None


class FrameworkInfoModel(BaseModel):
    name: str | None = None
    package: str | None = None
    version: str | None = None


class DependencyInfoModel(BaseModel):
    name: str
    version: str | None = None


class VersionDiscoveryModel(BaseModel):
    framework: FrameworkInfoModel
    language: VersionInfoModel
    runtime: VersionInfoModel
    package_manager: VersionInfoModel
    build_tools: list[VersionInfoModel]
    dependencies: list[DependencyInfoModel]
