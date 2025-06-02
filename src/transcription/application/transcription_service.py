import logging
from typing import Optional
from ..domain.transcription import Transcription
from src.shared.events.event_bus import EventBus
from src.storage.application.storage_service import StorageService
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.video_management.infrastructure.video_repository import VideoRepository

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(
            self,
            speech_adapter,
            storage_service: StorageService,
            event_bus: EventBus,
            transcription_repository: TranscriptionRepository,
            video_repository: VideoRepository
    ):
        self.speech_adapter = speech_adapter
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.transcription_repo = transcription_repository
        self.video_repo = video_repository

    async def process_transcription(self, video_id: str, file_path: str) -> Transcription:
        transcription: Optional[Transcription] = None
        video = None

        try:
            video = await self.video_repo.find_by_id(video_id)
            if not video:
                raise ValueError("Vídeo não encontrado")

            video.mark_as_processing()
            await self.video_repo.save(video)

            transcription = Transcription(video_id=video_id)
            await self.transcription_repo.save(transcription)

            audio_bytes = await self.storage_service.download(file_path)
            text = await self.speech_adapter.transcribe(audio_bytes)

            transcription.mark_as_completed(text)
            await self.transcription_repo.save(transcription)

            video.mark_as_completed()
            video.transcription_id = transcription.id
            await self.video_repo.save(video)

            await self.event_bus.publish("transcription_completed", {
                "video_id": video_id,
                "transcription_id": transcription.id
            })

            return transcription

        except Exception as e:
            logger.error(f"Erro ao processar transcrição do vídeo {video_id}: {e}", exc_info=True)
            if transcription:
                transcription.mark_as_failed(str(e))
                await self.transcription_repo.save(transcription)
            if video:
                video.mark_as_failed()
                await self.video_repo.save(video)
            raise
