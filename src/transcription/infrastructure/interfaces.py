from abc import ABC, abstractmethod
from typing import Optional


class ISpeechRecognition(ABC):

    @abstractmethod
    async def transcribe(self, file: bytes, language: str = "en") -> Optional[str]:
        """Transcribes an audio file to text, with an optional language hint."""
        pass
