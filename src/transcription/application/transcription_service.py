import logging
from typing import Optional

from src.transcription.domain.transcription import Transcription, TranscriptionStatus
from src.shared.events.event_bus import EventBus
from src.storage.application.storage_service import StorageService
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.video_management.application.video_service import VideoService
from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from src.video_management.domain.video import VideoStatus
from src.shared.utils.id_generator import generate_id

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(
            self,
            speech_recognition: ISpeechRecognition,
            storage_service: StorageService,
            event_bus: EventBus,
            transcription_repository: TranscriptionRepository,
            video_service: VideoService
    ):
        self.speech_recognition = speech_recognition
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.transcription_repo = transcription_repository
        self.video_service = video_service

    async def process_transcription(self, video_id: str) -> Transcription:
        """Process transcription for a video with robust error handling and idempotency"""
        try:
            # Get video and validate state
            video = await self.video_service.get_video_by_id(video_id)
            await self._validate_video_state(video)

            # Check for existing completed transcription
            existing_transcription = await self._get_existing_transcription(video_id)
            if existing_transcription and existing_transcription.text and \
               existing_transcription.status == TranscriptionStatus.COMPLETED:
                return existing_transcription

            transcription = existing_transcription

            # Create new transcription record if needed
            if transcription is None:
                transcription = await self._create_transcription_record(video_id)

            # Mark video as processing
            await self._update_video_processing(video_id)

            # Download and transcribe audio
            audio_bytes = await self._download_audio(video.file_path, video.id)
            text = await self._transcribe_audio(audio_bytes, video.id)

            # Finalize successful processing
            return await self._finalize_success(video_id, transcription, text)

        except Exception as e:
            await self._handle_failure(video_id, e)
            raise

    async def _validate_video_state(self, video):
        """Ensure video is in a valid state for processing"""
        if video.status == VideoStatus.PROCESSING:
            logger.warning(f"Video {video.id} is already being processed")
            raise RuntimeError(f"Video {video.id} is already being processed")

        if video.status == VideoStatus.FAILED:
            logger.info(f"Retrying processing for failed video {video.id}")

    async def _get_existing_transcription(self, video_id: str) -> Optional[Transcription]:
        """Check for existing completed transcription to avoid duplicate work"""
        transcription = await self.transcription_repo.find_by_video_id(video_id)
        if transcription and transcription.status == TranscriptionStatus.COMPLETED:
            logger.info(f"Using existing transcription for video {video_id}")
            return transcription
        return transcription

    async def _create_transcription_record(self, video_id: str) -> Transcription:
        """Create new transcription record in processing state"""
        new_transcription = Transcription(
            id=generate_id(),
            video_id=video_id,
            status=TranscriptionStatus.PROCESSING
        )
        return await self.transcription_repo.save(new_transcription)

    async def _update_video_processing(self, video_id: str):
        """Update video state to processing and persist"""
        await self.video_service.update_video_status(video_id=video_id, status=VideoStatus.PROCESSING)

    async def _download_audio(self, file_path: str, video_id: str) -> bytes:
        """Download audio with retry logic"""
        try:
            return await self.storage_service.download(file_path)
        except Exception as e:
            logger.error(f"Audio download failed for video {video_id}: {str(e)}")
            raise RuntimeError("Audio download failed") from e

    async def _transcribe_audio(self, audio_bytes: bytes, video_id: str) -> str:
        """Transcribe audio with error handling"""
        try:
            return await self.speech_recognition.transcribe(audio_bytes)
        except Exception as e:
            logger.error(f"Audio transcription failed for video {video_id}: {str(e)}")
            raise RuntimeError("Audio transcription failed") from e

    async def _finalize_success(
            self,
            video_id: str,
            transcription: Transcription,
            text: str
    ) -> Transcription:
        """Finalize successful transcription processing"""
        try:
            transcription.mark_as_completed(text)
            await self.transcription_repo.save(transcription)

            await self.video_service.update_video_status(video_id=video_id, status=VideoStatus.COMPLETED)
            await self._publish_success_event(video_id, transcription.id)

            logger.info(f"Transcription completed for video {video_id}")
            return transcription
        except Exception as e:
            logger.error(f"Finalization failed for video {video_id}: {str(e)}")
            raise RuntimeError("Finalization failed") from e

    async def _publish_success_event(self, video_id: str, transcription_id: str):
        """Publish success event with error handling"""
        try:
            await self.event_bus.publish("transcription_completed", {
                "video_id": video_id,
                "transcription_id": transcription_id
            })
        except Exception as e:
            logger.error(f"Event publishing failed for {video_id}: {str(e)}", exc_info=True)

    async def _handle_failure(self, video_id: str, error: Exception):
        """Handle failure scenarios consistently"""
        try:
            video = await self.video_service.get_video_by_id(video_id)
            if video:
                await self.video_service.update_video_status(video_id, VideoStatus.FAILED)

            transcription = await self.transcription_repo.find_by_video_id(video_id)
            if transcription:
                error_msg = str(error)[:500]
                transcription.mark_as_failed(error_msg)
                await self.transcription_repo.save(transcription)

            logger.error(f"Processing failed for video {video_id}: {str(error)}", exc_info=True)
        except Exception as inner_error:
            logger.critical(f"Failure handling crashed for {video_id}: {str(inner_error)}", exc_info=True)

    async def get_transcription_by_video(self, video_id: str) -> Transcription:
        return await self.transcription_repo.find_by_video_id(video_id=video_id)