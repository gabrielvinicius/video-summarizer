# src/transcription/application/transcription_service.py
import logging
import time
from typing import Optional

import structlog

from main import VIDEO_PROCESSING_DURATION, TRANSCRIPTIONS_TOTAL, TRANSCRIPTION_DURATION
from src.metrics.application.metrics_service import MetricsService
from src.transcription.domain.transcription import Transcription, TranscriptionStatus
from src.shared.events.event_bus import EventBus
from src.storage.application.storage_service import StorageService
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from src.shared.utils.id_generator import generate_id
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

    async def process_transcription(self, video_id: str) -> Transcription:
        start_time = time.time()
        logger.info("transcription.started", video_id=video_id)

        try:
            await self._publish_event("transcription_started", {"video_id": video_id})

            transcription = await self._get_existing_transcription(video_id)
            if transcription and transcription.text and transcription.status == TranscriptionStatus.COMPLETED:
                logger.info("transcription.completed", video_id=video_id, from_cache=True)
                await self._publish_event("transcription_completed", {
                    "video_id": transcription.video_id,
                    "transcription_id": transcription.id
                })
                return transcription

            if transcription is None:
                transcription = await self._create_transcription_record(video_id)

            audio_bytes = await self._download_audio(transcription.video_id)
            text = await self._transcribe_audio(audio_bytes, transcription.video_id)

            duration = time.time() - start_time
            self.metrics_service.increment_transcription('success')
            self.metrics_service.observe_transcription_duration(video_id, duration)

            logger.info("transcription.completed", video_id=video_id, duration=duration)

            return await self._finalize_success(video_id, transcription, text)

        except Exception as e:
            duration = time.time() - start_time
            self.metrics_service.increment_transcription('failure')
            logger.error("transcription.failed", video_id=video_id, error=str(e), duration=duration)
            await self._handle_failure(video_id, e)
            raise

    async def _get_existing_transcription(self, video_id: str) -> Optional[Transcription]:
        transcription = await self.transcription_repo.find_by_video_id(video_id)
        if transcription and transcription.status == TranscriptionStatus.COMPLETED:
            logger.info(f"Using existing transcription for video {video_id}")
            return transcription
        return transcription

    async def _create_transcription_record(self, video_id: str) -> Transcription:
        transcription = Transcription(
            id=generate_id(),
            video_id=video_id,
            status=TranscriptionStatus.PROCESSING
        )
        return await self.transcription_repo.save(transcription)

    async def _download_audio(self, video_id: str) -> bytes:
        video = await self.video_service.get_video_by_id(video_id)
        try:
            return await self.storage_service.download(video.file_path)
        except Exception as e:
            logger.error("transcription.download_failed", video_id=video_id, error=str(e))
            raise RuntimeError("Audio download failed") from e

    async def _transcribe_audio(self, audio_bytes: bytes, video_id: str) -> str:
        try:
            return await self.speech_recognition.transcribe(audio_bytes)
        except Exception as e:
            logger.error("transcription.transcribe_failed", video_id=video_id, error=str(e))
            raise RuntimeError("Transcription failed") from e

    async def _finalize_success(self, video_id: str, transcription: Transcription, text: str) -> Transcription:
        try:
            transcription.mark_as_completed(text)
            await self.transcription_repo.save(transcription)

            await self._publish_event("transcription_completed", {
                "video_id": video_id,
                "transcription_id": transcription.id
            })

            logger.info(f"Transcription completed for video {video_id}")
            return transcription
        except Exception as e:
            logger.error(f"Finalization failed for video {video_id}: {str(e)}")
            raise RuntimeError("Finalization failed") from e

    async def _handle_failure(self, video_id: str, error: Exception):
        try:
            transcription = await self.transcription_repo.find_by_video_id(video_id)
            if transcription:
                transcription.mark_as_failed(str(error)[:500])
                await self.transcription_repo.save(transcription)

            await self._publish_event("transcription_failed", {
                "video_id": video_id,
                "error": str(error)
            })

            logger.error(f"Processing failed for video {video_id}: {str(error)}", exc_info=True)
        except Exception as inner_error:
            logger.critical(f"Failure handling crashed for {video_id}: {str(inner_error)}", exc_info=True)

    async def _publish_event(self, event_name: str, payload: dict):
        try:
            await self.event_bus.publish(event_name, payload)
        except Exception as e:
            logger.error(f"Failed to publish event {event_name}: {str(e)}", exc_info=True)

    async def get_transcription_by_video(self, video_id: str) -> Transcription:
        return await self.transcription_repo.find_by_video_id(video_id)

    async def get_transcription_by_id(self, transcription_id: str) -> Transcription:
        return await self.transcription_repo.find_by_id(transcription_id)
