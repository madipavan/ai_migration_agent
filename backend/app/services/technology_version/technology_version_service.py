from app.services.technology_version.providers.flutter_provider import (
    FlutterProvider,
)
from app.services.technology_version.providers.npm_framework_provider import (
    NpmFrameworkProvider,
)
from app.services.technology_version.providers.python_provider import (
    PythonProvider,
)
from app.services.technology_version.providers.dotnet_provider import (
    DotNetProvider,
)


class TechnologyVersionService:

    def __init__(self):

        self.providers = {
            #
            # Flutter ecosystem
            #
            "flutter": FlutterProvider(),
            "dart": FlutterProvider(),
            #
            # Node ecosystem
            #
            "react": NpmFrameworkProvider(),
            "angular": NpmFrameworkProvider(),
            "vue": NpmFrameworkProvider(),
            "next.js": NpmFrameworkProvider(),
            "nestjs": NpmFrameworkProvider(),
            #
            # Python ecosystem
            #
            "python": PythonProvider(),
            "fastapi": PythonProvider(),
            "django": PythonProvider(),
            #
            # .NET ecosystem
            #
            ".net": DotNetProvider(),
            "asp.net": DotNetProvider(),
        }

    async def get_latest(self, technology: dict):
        name = (technology.get("name") or "").strip().lower()

        provider = self.providers.get(name)

        if provider:
            return await provider.get_latest(technology)

        return {
            "technology": technology.get("name"),
            "current_version": technology.get("version"),
            "latest_version": None,
            "supported": False,
            "message": f"No version provider available for '{technology.get('name')}'.",
        }
