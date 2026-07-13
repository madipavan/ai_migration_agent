import httpx

from .provider import VersionProvider


class PubDevProvider(VersionProvider):

    async def get_latest(
        self,
        package_name: str,
        current_version: str,
    ):

        url = f"https://pub.dev/api/packages/{package_name}"

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()

        return {
            "package": package_name,
            "current_version": current_version,
            "latest_version": data["latest"]["version"],
            "source": url,
        }
