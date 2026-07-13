import httpx

from .provider import VersionProvider


class NuGetProvider(VersionProvider):

    async def get_latest(
        self,
        package_name: str,
        current_version: str,
    ):

        index_url = (
            f"https://api.nuget.org/v3-flatcontainer/"
            f"{package_name.lower()}/index.json"
        )

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(index_url)
            response.raise_for_status()

        data = response.json()

        return {
            "package": package_name,
            "current_version": current_version,
            "latest_version": data["versions"][-1],
            "source": index_url,
        }
