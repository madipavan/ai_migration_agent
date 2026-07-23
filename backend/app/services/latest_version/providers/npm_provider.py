import httpx

from .provider import VersionProvider


class NpmProvider(VersionProvider):

    async def get_latest(
        self,
        package_name: str,
        current_version: str,
    ):

        print("Querying npm registry for '%s'", package_name)
        print(type(package_name))
        print(repr(package_name))
        url = f"https://registry.npmjs.org/{package_name}"

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)

        print("HTTP Status: %s", response.status_code)

        response.raise_for_status()

        data = response.json()

        latest = data["dist-tags"]["latest"]

        print(
            "npm latest version: %s -> %s",
            package_name,
            latest,
        )

        return {
            "package": package_name,
            "current_version": current_version,
            "latest_version": data["dist-tags"]["latest"],
            "source": url,
        }
