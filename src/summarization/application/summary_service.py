from typing import Optional
from ..domain.summary import Summary, SummaryStatus
from src.transcription.domain.transcription import TranscriptionStatus
from src.shared.events.event_bus import EventBus
from src.video_management.domain.video import VideoStatus


class SummaryService:
    def __init__(
            self,
            llm_adapter,  # Adaptador para OpenAI/HuggingFace
            event_bus: EventBus,
            summary_repository,
            transcription_repository,
            video_repository
    ):
        self.llm_adapter = llm_adapter
        self.event_bus = event_bus
        self.summary_repo = summary_repository
        self.transcription_repo = transcription_repository
        self.video_repo = video_repository

    async def generate_summary(self, transcription_id: str) -> Summary:
        """Gera um resumo a partir de uma transcrição."""
        try:
            # 1. Busca a transcrição
            transcription = self.transcription_repo.find_by_id(transcription_id)
            if not transcription or transcription.status != TranscriptionStatus.COMPLETED:
                raise ValueError("Transcrição inválida ou não processada")

            # 2. Cria a entidade Summary
            summary = Summary(
                id=generate_id(),
                transcription_id=transcription_id,
                video_id=transcription.video_id
            )
            self.summary_repo.save(summary)

            # 3. Gera o resumo usando LLM
            summary_text = await self.llm_adapter.generate_summary(transcription.text)

            # 4. Atualiza o resumo e o vídeo
            summary.mark_as_completed(summary_text)
            self.summary_repo.save(summary)

            video = self.video_repo.find_by_id(summary.video_id)
            video.summary_id = summary.id
            self.video_repo.save(video)

            # 5. Dispara evento de conclusão
            await self.event_bus.publish("summary_generated", {
                "video_id": summary.video_id,
                "summary_id": summary.id
            })

            return summary

        except Exception as e:
            summary.mark_as_failed(str(e))
            self.summary_repo.save(summary)
            raise
