from transformers import pipeline, AutoTokenizer
import torch
import asyncio
from threading import Lock

from src.summarization.infrastructure.interfaces import ISummarizer
from src.summarization.infrastructure.dependencies import register_summarizer


@register_summarizer("huggingface")
class HuggingFaceSummarizer(ISummarizer):
    def __init__(self, model_name="google-t5/t5-base"):
        """
        Initializes the summarizer with automatic device detection.
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.model_max_length = getattr(self.tokenizer, 'model_max_length', 1024)
        self.max_input_length = min(self.model_max_length, 512)
        self.max_summary_length = 64
        self.min_summary_length = 16

        self.summarizer = pipeline(
            "summarization",
            model=model_name,
            tokenizer=self.tokenizer,
            framework="pt",
            device=-1
        )

        self.device = self.summarizer.device
        print(f"HuggingFaceSummarizer initialized. Automatically selected device: {self.device}")

        self.lock = Lock()

    @property
    def provider_name(self) -> str:
        return "huggingface"

    def empty_device_cache(self):
        """Frees unused device memory, if applicable."""
        if self.device.type == 'cuda':
            torch.cuda.empty_cache()
        elif self.device.type == 'xpu':
            torch.xpu.empty_cache()

    def split_text_into_chunks(self, text: str) -> list[str]:
        """Splits the text into token-based chunks"""
        if not text.strip():
            return []

        tokens = self.tokenizer.tokenize(text)
        chunks = [
            tokens[i:i + self.max_input_length]
            for i in range(0, len(tokens), self.max_input_length)
        ]

        return [
            self.tokenizer.convert_tokens_to_string(chunk)
            for chunk in chunks
        ]

    async def summarize(self, text: str) -> str:
        """Processes the text in chunks and returns the concatenated summary"""
        if not text.strip():
            return ""

        self.empty_device_cache()

        chunks = self.split_text_into_chunks(text)
        summaries = []

        for chunk in chunks:
            summary = await self._summarize_chunk(chunk)
            summaries.append(summary)

        self.empty_device_cache()

        return " ".join(summaries)

    async def _summarize_chunk(self, chunk: str) -> str:
        """Processes an individual chunk with robust error handling"""
        with self.lock:
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(
                    None,
                    lambda: self.summarizer(
                        chunk,
                        max_length=self.max_summary_length,
                        min_length=self.min_summary_length,
                        do_sample=False,
                        num_beams=4,
                        truncation=True,
                        no_repeat_ngram_size=3
                    )[0]['summary_text']
                )
            except Exception as e:
                print(f"Error summarizing chunk: {str(e)}")
                return ""
