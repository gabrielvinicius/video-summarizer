# src/storage/infrastructure/local_storage_service.py
from src.storage.application.storage_service import StorageService, StorageException
from src.storage.infrastructure.dependencies import register_storage
from pathlib import Path
from typing import Union, Optional, Tuple
import asyncio


@register_storage("local")
class LocalStorageService(StorageService):
    def __init__(self):
        self.root = Path("storage")
        self.root.mkdir(exist_ok=True, parents=True)

    @property
    def provider_name(self) -> str:
        return "local"

    async def upload(self, file_path: Union[str, Path], file: bytes) -> bool:
        path = self.root / file_path
        try:
            await asyncio.to_thread(self._sync_upload, path, file)
            return True
        except Exception as e:
            raise StorageException("Error saving file locally", e)

    def _sync_upload(self, path: Path, file: bytes):
        """Synchronous implementation of the upload."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file)

    async def download(self, file_path: Union[str, Path]) -> Optional[Tuple[bytes, str]]:
        path = self.root / file_path
        try:
            content = await asyncio.to_thread(self._sync_download, path)
            return content, path.name
        except FileNotFoundError:
            return None
        except Exception as e:
            raise StorageException("Error reading file locally", e)

    def _sync_download(self, path: Path) -> bytes:
        """Synchronous implementation of the download."""
        return path.read_bytes()

    async def delete(self, file_path: Union[str, Path]) -> bool:
        path = self.root / file_path
        try:
            return await asyncio.to_thread(self._sync_delete, path)
        except FileNotFoundError:
            return False
        except Exception as e:
            raise StorageException("Error deleting file locally", e)

    def _sync_delete(self, path: Path) -> bool:
        """Synchronous implementation of the delete."""
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, file_path: Union[str, Path]) -> bool:
        path = self.root / file_path
        return await asyncio.to_thread(path.exists)
