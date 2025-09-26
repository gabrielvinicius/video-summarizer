# tests/mocks/in_memory_storage.py
from typing import Dict, Optional, Tuple
from src.storage.application.storage_service import StorageService


class InMemoryStorage(StorageService):
    def __init__(self):
        self.files: Dict[str, bytes] = {}

    async def upload(self, file_path: str, file: bytes) -> None:
        self.files[file_path] = file

    async def download(self, file_path: str) -> Optional[Tuple[bytes, str]]:
        file_content = self.files.get(file_path)
        if file_content:
            return file_content, file_path.split("/")[-1]
        return None

    async def delete(self, file_path: str) -> bool:
        if file_path in self.files:
            del self.files[file_path]
            return True
        return False

    async def exists(self, file_path: str) -> bool:
        return file_path in self.files
