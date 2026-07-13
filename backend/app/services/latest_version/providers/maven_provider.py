import httpx

from .provider import VersionProvider


class MavenProvider(VersionProvider):

    async def get_latest(
        self,
        package_name: str,
        current_version: str,
    ):

        group_id, artifact_id = package_name.split(":")

        url = (
            "https://search.maven.org/solrsearch/select"
            f"?q=g:{group_id}+AND+a:{artifact_id}"
            "&rows=1"
            "&wt=json"
        )

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()

        latest = data["response"]["docs"][0]["latestVersion"]

        return {
            "package": package_name,
            "current_version": current_version,
            "latest_version": latest,
            "source": url,
        }
