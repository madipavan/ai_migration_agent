import httpx

from .provider import TechnologyVersionProvider


class FlutterProvider(TechnologyVersionProvider):

    async def get_latest(
        self,
        technology: dict,
    ):

        url = (
            "https://storage.googleapis.com/"
            "flutter_infra_release/releases/releases_linux.json"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        data = response.json()

        latest = data["current_release"]["stable"]

        release = next(x for x in data["releases"] if x["hash"] == latest)

        return {
            "technology": technology["name"],
            "current_version": technology["version"],
            "latest_version": release["version"],
            "source": url,
        }
