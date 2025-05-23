# infrastructure/huggingface_adapter.py
from transformers import pipeline


class HuggingFaceSummarizer:
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        self.pipeline = pipeline("summarization", model=model_name)

    async def generate_summary(self, text: str) -> str:
        result = self.pipeline(text, max_length=150)
        return result[0]["summary_text"]
