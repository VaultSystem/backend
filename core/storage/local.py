from pathlib import Path

from core.settings import settings

from .base import Storage


class LocalStorage(Storage):
    def __init__(self, base_path: Path = Path(settings.MEDIA_URL)):
        self.base_path = base_path
        self.base_path.mkdir(exist_ok=True)

    async def upload(self, file_name: str, data: bytes) -> str:
        file_path = self.base_path / file_name
        file_path.write_bytes(data)
        return str(file_path)

    async def download(self, file_name: str) -> bytes:
        file_path = self.base_path / file_name
        return file_path.read_bytes()

    async def delete(self, file_name: str) -> None:
        file_path = self.base_path / file_name
        if file_path.exists():
            file_path.unlink()
