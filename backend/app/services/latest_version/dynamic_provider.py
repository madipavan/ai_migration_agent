import httpx


class DynamicProvider:

    async def get_latest(
        self,
        package_name: str,
        current_version: str,
        source: dict,
    ):

        url = source["url"]

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()

        #
        # Example:
        # version_path = "dist-tags.latest"
        #
        value = data

        for key in source["version_path"].split("."):
            value = value[key]

        return {
            "package": package_name,
            "current_version": current_version,
            "latest_version": value,
            "source": url,
        }
