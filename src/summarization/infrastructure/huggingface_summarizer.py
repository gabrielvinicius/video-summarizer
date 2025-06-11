# src/summarization/infrastructure/huggingface_summarizer.py

from transformers import pipeline
from src.summarization.infrastructure.interfaces import ISummarizer
import asyncio
import logging

logger = logging.getLogger(__name__)


class HuggingFaceSummarizer(ISummarizer):
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        # Carregamento pesado no init síncrono — só uma vez
        self.summarizer = pipeline("summarization", model=model_name)

    async def summarize(self, text: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            chunks = self._split_into_chunks(text, max_tokens=1024)
            summaries = await asyncio.gather(*[
                loop.run_in_executor(None, self._summarize_chunk, chunk)
                for chunk in chunks
            ])
            return " ".join(summaries)
        except Exception as e:
            logger.error(f"HuggingFace summarization failed: {e}")
            raise

    def _summarize_chunk(self, chunk: str) -> str:
        result = self.summarizer(chunk, max_length=150, min_length=30, do_sample=False)
        return result[0]["summary_text"]

    def _split_into_chunks(self, text: str, max_tokens: int = 1024) -> list[str]:
        # Quebra segura por parágrafos ou frases longas
        import textwrap
        paragraphs = text.split("\n")
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) < max_tokens:
                current += " " + para
            else:
                chunks.append(current.strip())
                current = para
        if current:
            chunks.append(current.strip())
        return chunks
