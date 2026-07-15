import httpx

from .provider import TechnologyVersionProvider

PACKAGE_MAP = {
    "react": "react",
    "angular": "@angular/core",
    "vue": "vue",
    "next.js": "next",
    "nestjs": "@nestjs/core",
}


class NpmFrameworkProvider(TechnologyVersionProvider):

    async def get_latest(self, technology: dict):

        framework = technology["name"].lower()

        package = PACKAGE_MAP.get(framework)

        if not package:
            raise ValueError(f"No npm package mapping for {framework}")

        url = f"https://registry.npmjs.org/{package}"

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()

        return {
            "technology": technology["name"],
            "current_version": technology["version"],
            "latest_version": data["dist-tags"]["latest"],
            "source": url,
        }
