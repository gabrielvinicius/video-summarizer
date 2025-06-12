import asyncio
from transformers import pipeline
from threading import Lock


class HuggingFaceSummarizer:
    def __init__(self, model_name="facebook/bart-large-cnn"):
        self.model_name = model_name
        self.summarizer = pipeline("summarization", model=model_name)
        self.lock = Lock()

    def split_text_into_chunks(self, text, chunk_size=512):
        if not text:
            return []

        words = text.split()
        return [
            " ".join(words[i:i + chunk_size])
            for i in range(0, len(words), chunk_size)
        ]

    async def summarize(self, text: str) -> str:
        chunks = self.split_text_into_chunks(text)
        if not chunks:
            return ""

        summaries = []
        for chunk in chunks:
            summary = await self._summarize_chunk(chunk)
            summaries.append(summary)

        return " ".join(summaries)

    async def _summarize_chunk(self, chunk: str) -> str:
        with self.lock:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.summarizer(
                    chunk,
                    max_length=150,
                    min_length=30,
                    do_sample=False,
                    truncation=True  # Garantir truncamento
                )[0]['summary_text']
            )
            return result