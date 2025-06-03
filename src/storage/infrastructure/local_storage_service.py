from src.storage.application.storage_service import StorageService, StorageException
from src.storage.infrastructure.dependencies import register_storage
from pathlib import Path
from typing import Union, Optional
import asyncio

@register_storage("local")
class LocalStorageService(StorageService):
    def __init__(self):
        self.root = Path("storage")
        self.root.mkdir(exist_ok=True, parents=True)

    async def upload(self, file_path: Union[str, Path], file: bytes) -> None:
        path = self.root / file_path
        try:
            # Executa em thread separada
            await asyncio.to_thread(self._sync_upload, path, file)
        except Exception as e:
            raise StorageException("Erro ao salvar localmente", e)

    def _sync_upload(self, path: Path, file: bytes):
        """Implementação síncrona do upload"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file)

    async def download(self, file_path: Union[str, Path]) -> Optional[bytes]:
        path = self.root / file_path
        try:
            # Executa em thread separada
            return await asyncio.to_thread(self._sync_download, path)
        except FileNotFoundError:
            return None
        except Exception as e:
            raise StorageException("Erro ao ler localmente", e)

    def _sync_download(self, path: Path) -> bytes:
        """Implementação síncrona do download"""
        return path.read_bytes()

    async def delete(self, file_path: Union[str, Path]) -> bool:
        path = self.root / file_path
        try:
            # Executa em thread separada
            return await asyncio.to_thread(self._sync_delete, path)
        except FileNotFoundError:
            return False
        except Exception as e:
            raise StorageException("Erro ao deletar localmente", e)

    def _sync_delete(self, path: Path) -> bool:
        """Implementação síncrona do delete"""
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, file_path: Union[str, Path]) -> bool:
        path = self.root / file_path
        return await asyncio.to_thread(path.exists)