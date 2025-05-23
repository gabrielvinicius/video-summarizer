from openai import OpenAI
from typing import Optional

class OpenAISummarizer:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def generate_summary(self, text: str) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"Resuma o seguinte texto de forma concisa:\n\n{text}"
                }],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Falha na geração do resumo: {str(e)}")