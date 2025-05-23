import whisper
from typing import Optional
import tempfile


class WhisperTranscriber:
    def __init__(self, model_name: str = "base"):
        self.model = whisper.load_model(model_name)

    async def transcribe(self, audio_bytes: bytes) -> Optional[str]:
        try:
            # Salva os bytes em um arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                result = self.model.transcribe(tmp.name)
                return result["text"]
        except Exception as e:
            raise RuntimeError(f"Falha na transcrição: {str(e)}")
