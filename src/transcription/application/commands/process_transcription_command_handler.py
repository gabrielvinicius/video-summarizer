# src/transcription/application/commands/process_transcription_command_handler.py
import time
import structlog

from src.metrics.application.metrics_service import MetricsService
from src.shared.events.domain_events import TranscriptionCompleted, TranscriptionFailed, TranscriptionStarted
from src.shared.events.event_bus import EventBus
from src.storage.application.storage_service import StorageService
from src.transcription.domain.transcription import Transcription, TranscriptionStatus
from src.transcription.infrastructure.interfaces import ISpeechRecognition
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
# Import correct CQRS dependencies
from src.video_management.application.queries.video_queries import VideoQueries
from src.video_management.infrastructure.video_repository import VideoRepository
from .process_transcription_command import ProcessTranscriptionCommand

logger = structlog.get_logger(__name__)


class ProcessTranscriptionCommandHandler:
    def __init__(
        self,
        speech_recognition: ISpeechRecognition,
        storage_service: StorageService,
        event_bus: EventBus,
        transcription_repository: TranscriptionRepository,
        video_queries: VideoQueries, # Correct read dependency
        video_repository: VideoRepository, # Correct write dependency
        metrics_service: MetricsService,
    ):
        self.speech_recognition = speech_recognition
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.transcription_repo = transcription_repository
        self.video_queries = video_queries
        self.video_repository = video_repository
        self.metrics_service = metrics_service

    async def handle(self, command: ProcessTranscriptionCommand) -> Transcription:
        start_time = time.time()
        logger.info("transcription.started", video_id=command.video_id, provider=command.provider, language=command.language)

        video = await self.video_queries.get_by_id(command.video_id)
        if not video:
            raise ValueError(f"Video with id {command.video_id} not found.")

        transcription = await self.transcription_repo.find_by_video_id(command.video_id)

        try:
            video.process() # Use the state pattern to transition
            await self.video_repository.save(video)
            await self.event_bus.publish(TranscriptionStarted(video_id=command.video_id))

            if transcription and transcription.text and transcription.status == TranscriptionStatus.COMPLETED:
                video.complete() # Ensure video state is consistent
                await self.video_repository.save(video)
                logger.info("transcription.completed", video_id=command.video_id, from_cache=True)
                await self.event_bus.publish(TranscriptionCompleted(video_id=transcription.video_id, transcription_id=str(transcription.id)))
                return transcription

            if transcription is None:
                transcription = Transcription(video_id=command.video_id, status=TranscriptionStatus.PROCESSING, provider=command.provider)
            else:
                transcription.provider = command.provider
            
            await self.transcription_repo.save(transcription)

            audio_bytes = await self.storage_service.download(video.file_path)
            text = await self.speech_recognition.transcribe(audio_bytes[0], language=command.language)

            transcription.mark_as_completed(text)
            await self.transcription_repo.save(transcription)
            
            video.complete() # Use the state pattern to transition
            await self.video_repository.save(video)

            await self.event_bus.publish(TranscriptionCompleted(video_id=command.video_id, transcription_id=str(transcription.id)))

            duration = time.time() - start_time
            self.metrics_service.increment_transcription('success')
            self.metrics_service.observe_transcription_duration(video_id=command.video_id, duration=duration, provider=self.speech_recognition.provider_name)

            logger.info("transcription.completed", video_id=command.video_id, duration=duration)
            return transcription

        except Exception as e:
            duration = time.time() - start_time
            self.metrics_service.increment_transcription('failure')
            logger.error("transcription.failed", video_id=command.video_id, error=str(e), duration=duration)

            if video:
                video.fail(str(e)[:500]) # Use the state pattern to transition
                await self.video_repository.save(video)

            if transcription:
                transcription.mark_as_failed(str(e)[:500])
                await self.transcription_repo.save(transcription)

            await self.event_bus.publish(TranscriptionFailed(video_id=command.video_id, error=str(e)))
            raise
