from app.services.latest_version.providers.npm_provider import NpmProvider
from app.services.latest_version.providers.pypi_provider import PyPiProvider
from app.services.latest_version.providers.maven_provider import MavenProvider
from app.services.latest_version.providers.nuget_provider import NuGetProvider
from app.services.latest_version.providers.pubdev_provider import PubDevProvider

from app.agents.official_source_discovery_agent import (
    OfficialSourceDiscoveryAgent,
)

from app.services.latest_version.dynamic_provider import DynamicProvider


class LatestVersionService:

    def __init__(self, llm):

        self.providers = {
            "npm": NpmProvider(),
            "yarn": NpmProvider(),
            "pnpm": NpmProvider(),
            "pypi": PyPiProvider(),
            "pip": PyPiProvider(),
            "maven": MavenProvider(),
            "gradle": MavenProvider(),
            "nuget": NuGetProvider(),
            "pub": PubDevProvider(),
        }

        self.dynamic_provider = DynamicProvider()

        self.discovery_agent = OfficialSourceDiscoveryAgent(llm=llm)

    async def discover(
        self,
        framework: dict,
        package_manager: dict,
    ):

        manager = package_manager.get("name", "").strip().lower()

        package_name = framework.get("package")
        current_version = framework.get("version")

        provider = self.providers.get(manager)

        #
        # Known package manager
        #
        if provider:

            return await provider.get_latest(
                package_name=package_name,
                current_version=current_version,
            )

        #
        # Unknown ecosystem
        #
        source = await self.discovery_agent.discover(
            framework=framework,
            package_manager=package_manager,
        )

        return await self.dynamic_provider.get_latest(
            package_name=package_name,
            current_version=current_version,
            source=source,
        )
