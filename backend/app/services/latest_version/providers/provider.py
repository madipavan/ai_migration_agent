# provider.py

from abc import ABC, abstractmethod


class VersionProvider(ABC):

    @abstractmethod
    async def get_latest(
        self,
        package_name: str,
        current_version: str,
    ):
        pass
