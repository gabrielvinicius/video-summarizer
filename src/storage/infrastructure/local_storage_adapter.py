# src/video_management/infrastructure/storage_adapter.py
from src.storage.application.storage_service import StorageService


class VideoStorageAdapter(StorageService):
    async def upload(self, file_path: str, file: bytes):
        # Implementação específica para vídeos (ex: chunked upload)
        pass
