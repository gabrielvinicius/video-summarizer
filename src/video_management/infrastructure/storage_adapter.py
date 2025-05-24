#from src.storage.application.storage_service import StorageService
from typing import Optional
import aiofiles
import os

class LocalStorageAdapter():
    def __init__(self, base_path: str = "uploads"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def upload(self, file_path: str, file: bytes) -> None:
        full_path = os.path.join(self.base_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        async with aiofiles.open(full_path, "wb") as buffer:
            await buffer.write(file)

    async def download(self, file_path: str) -> Optional[bytes]:
        full_path = os.path.join(self.base_path, file_path)
        if os.path.exists(full_path):
            async with aiofiles.open(full_path, "rb") as buffer:
                return await buffer.read()
        return None