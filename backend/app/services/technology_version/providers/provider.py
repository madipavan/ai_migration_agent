from abc import ABC, abstractmethod


class TechnologyVersionProvider(ABC):

    @abstractmethod
    async def get_latest(
        self,
        technology: dict,
    ) -> dict:
        pass
