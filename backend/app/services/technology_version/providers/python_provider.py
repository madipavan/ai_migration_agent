import httpx

from .provider import TechnologyVersionProvider

PACKAGE_MAP = {
    "fastapi": "fastapi",
    "django": "django",
}


class PythonProvider(TechnologyVersionProvider):

    async def get_latest(self, technology: dict):

        name = technology["name"].lower()

        #
        # Python language
        #
        if name == "python":

            url = "https://endoflife.date/api/python.json"

            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(url)
                response.raise_for_status()

            latest = response.json()[0]["latest"]

            return {
                "technology": "Python",
                "current_version": technology["version"],
                "latest_version": latest,
                "source": url,
            }

        #
        # PyPI packages
        #
        package = PACKAGE_MAP.get(name)

        if not package:
            raise ValueError(f"No PyPI mapping for {name}")

        url = f"https://pypi.org/pypi/{package}/json"

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()

        data = response.json()

        return {
            "technology": technology["name"],
            "current_version": technology["version"],
            "latest_version": data["info"]["version"],
            "source": url,
        }
