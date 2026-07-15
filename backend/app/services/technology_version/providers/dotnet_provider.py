import httpx

from .provider import TechnologyVersionProvider


class DotNetProvider(TechnologyVersionProvider):

    async def get_latest(self, technology: dict):

        url = "https://dotnetcli.blob.core.windows.net/dotnet/release-metadata/releases-index.json"

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()

        latest = data["releases-index"][0]["latest-release"]

        return {
            "technology": technology["name"],
            "current_version": technology["version"],
            "latest_version": latest,
            "source": url,
        }
