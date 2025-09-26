# src/transcription/application/transcription_service.py
import time
from typing import Optional

import structlog

from src.metrics.application.metrics_service import MetricsService
# Importação dos eventos de domínio tipados
from src.shared.events.domain_events import TranscriptionCompleted, TranscriptionFailed, TranscriptionStarted
from src.shared.events.event_bus import EventBus
from src.storage.application.storage_service import StorageService
from src.transcription.domain.transcription import Transcription, TranscriptionStatus
from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.video_management.application.video_service import VideoService

logger = structlog.get_logger(__name__)


class TranscriptionService:
    def __init__(
            self,
            speech_recognition: ISpeechRecognition,
            storage_service: StorageService,
            event_bus: EventBus,
            transcription_repository: TranscriptionRepository,
            video_service: VideoService,
            metrics_service: MetricsService,
    ):
        self.speech_recognition = speech_recognition
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.transcription_repo = transcription_repository
        self.video_service = video_service
        self.metrics_service = metrics_service

    async def process_transcription(self, video_id: str, language: str = "en") -> Transcription:
        start_time = time.time()
        logger.info("transcription.started", video_id=video_id, language=language)

        transcription = await self.transcription_repo.find_by_video_id(video_id)

        try:
            await self.event_bus.publish(TranscriptionStarted(video_id=video_id))

            if transcription and transcription.text and transcription.status == TranscriptionStatus.COMPLETED:
                logger.info("transcription.completed", video_id=video_id, from_cache=True)
                await self.event_bus.publish(TranscriptionCompleted(
                    video_id=transcription.video_id,
                    transcription_id=str(transcription.id)
                ))
                return transcription

            if transcription is None:
                transcription = Transcription(video_id=video_id, status=TranscriptionStatus.PROCESSING)
                await self.transcription_repo.save(transcription)

            audio_bytes = await self._download_audio(transcription.video_id)
            # Passa o parâmetro de idioma para o serviço de transcrição
            text = await self.speech_recognition.transcribe(audio_bytes, language=language)

            transcription.mark_as_completed(text)
            await self.transcription_repo.save(transcription)

            await self.event_bus.publish(TranscriptionCompleted(
                video_id=video_id,
                transcription_id=str(transcription.id)
            ))

            duration = time.time() - start_time
            self.metrics_service.increment_transcription('success')
            self.metrics_service.observe_transcription_duration(video_id, duration)

            logger.info("transcription.completed", video_id=video_id, duration=duration)
            return transcription

        except Exception as e:
            duration = time.time() - start_time
            self.metrics_service.increment_transcription('failure')
            logger.error("transcription.failed", video_id=video_id, error=str(e), duration=duration)

            if transcription:
                transcription.mark_as_failed(str(e)[:500])
                await self.transcription_repo.save(transcription)

            await self.event_bus.publish(TranscriptionFailed(video_id=video_id, error=str(e)))
            raise

    async def _download_audio(self, video_id: str) -> bytes:
        video = await self.video_service.get_video_by_id(video_id)
        if not video:
            raise ValueError(f"Video with id {video_id} not found.")
        try:
            content, _ = await self.storage_service.download(video.file_path)
            return content
        except Exception as e:
            logger.error("transcription.download_failed", video_id=video_id, error=str(e))
            raise RuntimeError("Audio download failed") from e

    async def get_transcription_by_video(self, video_id: str) -> Optional[Transcription]:
        return await self.transcription_repo.find_by_video_id(video_id)

    async def get_transcription_by_id(self, transcription_id: str) -> Optional[Transcription]:
        return await self.transcription_repo.find_by_id(transcription_id)
