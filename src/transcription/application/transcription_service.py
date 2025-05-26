from typing import Optional
from ..domain.transcription import Transcription, TranscriptionStatus
from src.video_management.domain.video import VideoStatus
from src.shared.events.event_bus import EventBus
from src.storage.application.storage_service import StorageService
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository
from src.video_management.infrastructure.video_repository import VideoRepository


class TranscriptionService:
    def __init__(
            self,
            speech_adapter,  # Adaptador para Whisper/Google
            storage_service: StorageService,
            event_bus: EventBus,
            transcription_repository: TranscriptionRepository ,
            video_repository : VideoRepository
    ):
        self.speech_adapter = speech_adapter
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.transcription_repo = transcription_repository
        self.video_repo = video_repository

    async def process_transcription(self, video_id: str, file_path: str) -> Transcription:
        """Processa o áudio/vídeo e salva a transcrição."""
        try:
            # 1. Busca o vídeo e atualiza status
            video = self.video_repo.find_by_id(video_id)
            if not video:
                raise ValueError("Vídeo não encontrado")

            video.mark_as_processing()
            self.video_repo.save(video)

            # 2. Cria a entidade Transcription
            transcription = Transcription(id=generate_id(), video_id=video_id)
            self.transcription_repo.save(transcription)

            # 3. Faz download do arquivo
            audio_bytes = await self.storage_service.download(file_path)

            # 4. Chama o serviço de transcrição
            text = await self.speech_adapter.transcribe(audio_bytes)

            # 5. Atualiza a transcrição e o vídeo
            transcription.mark_as_completed(text)
            self.transcription_repo.save(transcription)

            video.mark_as_completed()
            video.transcription_id = transcription.id
            self.video_repo.save(video)

            # 6. Dispara evento para o módulo de resumo
            await self.event_bus.publish("transcription_completed", {
                "video_id": video_id,
                "transcription_id": transcription.id
            })

            return transcription

        except Exception as e:
            # Tratamento de erros
            transcription.mark_as_failed(str(e))
            self.transcription_repo.save(transcription)
            video.mark_as_failed()
            self.video_repo.save(video)
            raise