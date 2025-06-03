import whisper
from typing import Optional
import tempfile

from src.transcription.infrastructure.speech_recognition import ISpeechRecognition


class WhisperTranscriber(ISpeechRecognition):
    def __init__(self, model_name: str = "base"):
        self.model = whisper.load_model(model_name)

    async def transcribe(self, file: bytes) -> Optional[str]:
        try:
            # Salva os bytes em um arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
                tmp.write(file)
                tmp.flush()
                result = self.model.transcribe(tmp.name)
                return result["text"]
        except Exception as e:
            raise RuntimeError(f"Falha na transcrição: {str(e)}")
