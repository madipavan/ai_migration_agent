from typing import Any, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr


class LatestVersionInput(BaseModel):
    package_name: str = Field(
        ...,
        description="The name of the dependency package to check (e.g., 'provider', 'bloc', 'Newtonsoft.Json')",
    )
    current_version: str = Field(
        ...,
        description="The current version of the dependency package to check (e.g., '16.2.1')",
    )


class LatestVersionTool(BaseTool):
    name: str = "Latest Version Resolver"
    description: str = (
        "Returns the latest stable version of a package from the official registry."
    )
    args_schema: Type[BaseModel] = LatestVersionInput

    _service: Any = PrivateAttr()
    _framework: dict = PrivateAttr()
    _package_manager: dict = PrivateAttr()

    def __init__(
        self, service: Any, framework: dict, package_manager: dict, **data: Any
    ):
        super().__init__(**data)
        self._service = service
        self._framework = framework
        self._package_manager = package_manager

    def _run(self, package_name: str, current_version: str):
        print("inside tool")
        # Pass the pre-configured environments along with the requested package name
        return self._service.get_latest_version(
            framework=self._framework,
            package_manager=self._package_manager,
            package_name=package_name,
            current_version=current_version,
        )
