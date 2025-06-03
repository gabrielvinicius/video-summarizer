import logging
from typing import Optional
from src.transcription.domain.transcription import Transcription
from src.shared.events.event_bus import EventBus
from src.storage.application.storage_service import StorageService
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.video_management.infrastructure.video_repository import VideoRepository
from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from src.video_management.domain.video import Video

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(
            self,
            speech_recognition: ISpeechRecognition,
            storage_service: StorageService,
            event_bus: EventBus,
            transcription_repository: TranscriptionRepository,
            video_repository: VideoRepository
    ):
        self.speech_recognition = speech_recognition
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.transcription_repo = transcription_repository
        self.video_repo = video_repository

    async def process_transcription(self, video_id: str) -> Transcription:
        """Process video transcription with comprehensive error handling and state management."""
        try:
            # 1. Validate and prepare video
            video = await self._validate_and_prepare_video(video_id)

            # 2. Create transcription record
            transcription = await self._create_transcription_record(video_id)

            # 3. Process transcription
            text = await self._process_audio_transcription(video)

            # 4. Finalize successful processing
            return await self._finalize_successful_processing(video, transcription, text)

        except Exception as e:
            await self._handle_processing_failure(video_id, e)
            raise

    async def _validate_and_prepare_video(self, video_id: str) -> Video:
        """Validate video exists and mark as processing."""
        video = await self.video_repo.find_by_id(video_id)
        if not video:
            raise ValueError(f"Video not found: {video_id}")

        video.mark_as_processing()
        await self.video_repo.save(video)
        return video

    async def _create_transcription_record(self, video_id: str) -> Transcription:
        """Create initial transcription record."""
        transcription = Transcription(video_id=video_id)
        await self.transcription_repo.save(transcription)
        return transcription

    async def _process_audio_transcription(self, video: Video) -> str:
        """Download audio and perform speech recognition."""
        try:
            audio_bytes = await self.storage_service.download(video.file_path)
            return await self.speech_recognition.transcribe(audio_bytes)
        except Exception as e:
            logger.error(f"Audio processing failed for video {video.id}", exc_info=True)
            raise RuntimeError(f"Audio processing failed: {str(e)}") from e

    async def _finalize_successful_processing(
            self,
            video: Video,
            transcription: Transcription,
            text: str
    ) -> Transcription:
        """Complete the successful transcription process."""
        transcription.mark_as_completed(text)
        await self.transcription_repo.save(transcription)

        video.mark_as_completed()
        video.transcription_id = transcription.id
        await self.video_repo.save(video)

        await self._publish_success_event(video.id, transcription.id)

        return transcription

    async def _publish_success_event(self, video_id: str, transcription_id: str):
        """Publish transcription completed event."""
        try:
            await self.event_bus.publish("transcription_completed", {
                "video_id": video_id,
                "transcription_id": transcription_id
            })
        except Exception as e:
            logger.warning(f"Failed to publish event for {video_id}: {e}")

    async def _handle_processing_failure(self, video_id: str, error: Exception):
        """Handle all failure scenarios."""
        try:
            # Attempt to update video status
            video = await self.video_repo.find_by_id(video_id)
            if video:
                video.mark_as_failed()
                await self.video_repo.save(video)

            # Attempt to update transcription status if exists
            transcription = await self.transcription_repo.find_by_video_id(video_id)
            if transcription:
                transcription.mark_as_failed(str(error))
                await self.transcription_repo.save(transcription)

        except Exception as inner_error:
            logger.error(f"Failed to handle processing failure for {video_id}: {inner_error}", exc_info=True)