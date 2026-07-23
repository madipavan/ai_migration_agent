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

    async def get_latest_version(
        self,
        framework: dict,
        package_manager: dict,
        package_name: str,
        current_version: str,
    ):

        manager = package_manager.get("name", "").strip().lower()

        print("=" * 80)
        print("Latest Version Lookup Started")
        print("Package Manager : %s", manager)
        print("Package         : %s", package_name)
        print("Current Version : %s", current_version)

        provider = self.providers.get(manager)

        #
        # Known package manager
        #
        if provider:
            print(
                "Using official provider: %s",
                provider.__class__.__name__,
            )

            try:
                result = await provider.get_latest(
                    package_name=package_name,
                    current_version=current_version,
                )

                print(
                    "Latest version found: %s",
                    result.get("latest_version"),
                )

                print(
                    "Official source: %s",
                    result.get("source"),
                )

                print("Lookup completed successfully.")
                print("=" * 80)

                return result

            except Exception:
                print(
                    "Official provider lookup failed for '%s'",
                    package_name,
                )
                raise

        #
        # Unknown ecosystem
        #
        print(
            "No provider registered for package manager '%s'.",
            manager,
        )
        print("Attempting official source discovery...")

        source = await self.discovery_agent.discover(
            framework=framework,
            package_manager=package_manager,
        )

        print("Discovered source: %s", source)

        print("Attempting dynamic version lookup...")

        result = await self.dynamic_provider.get_latest(
            package_name=package_name,
            current_version=current_version,
            source=source,
        )

        print(
            "Dynamic lookup result: %s",
            result.get("latest_version"),
        )

        print("=" * 80)

        return result
