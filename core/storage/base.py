from abc import ABC, abstractmethod


class Storage(ABC):
    @abstractmethod
    async def upload(self, file_name: str, data: bytes) -> str:
        pass

    @abstractmethod
    async def download(self, file_name: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, file_name: str) -> None:
        pass
