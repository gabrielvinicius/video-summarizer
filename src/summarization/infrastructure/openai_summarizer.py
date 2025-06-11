# src/summarization/infrastructure/openai_summarizer.py
from src.summarization.infrastructure.interfaces import ISummarizer
import openai


class OpenAISummarizer(ISummarizer):
    async def summarize(self, text: str) -> str:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Resuma o seguinte texto:"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message["content"].strip()
