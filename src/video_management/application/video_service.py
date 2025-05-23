from uuid import uuid4
from datetime import datetime
from typing import Optional
from src.video_management.domain.video import Video, VideoStatus
from src.storage.application.storage_service import StorageService
from src.shared.events.event_bus import EventBus


class VideoService:
    def __init__(
            self,
            storage_service: StorageService,
            event_bus: EventBus,
            video_repository
    ):
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.video_repository = video_repository

    async def upload_video(self, user_id: str, file: bytes, filename: str) -> Video:
        """Faz upload de um vídeo e dispara o evento de processamento."""
        video_id = str(uuid4())
        file_path = f"videos/{user_id}/{video_id}/{filename}"

        # Salva o arquivo no storage (S3, local, etc.)
        await self.storage_service.upload(file_path, file)

        # Cria e persiste a entidade Video
        video = Video(
            id=video_id,
            user_id=user_id,
            file_path=file_path,
            status=VideoStatus.UPLOADED
        )
        self.video_repository.save(video)

        # Dispara evento para processamento assíncrono
        await self.event_bus.publish("video_uploaded", {
            "video_id": video_id,
            "file_path": file_path,
            "user_id": user_id
        })

        return video

    def get_video_by_id(self, video_id: str) -> Optional[Video]:
        return self.video_repository.find_by_id(video_id)