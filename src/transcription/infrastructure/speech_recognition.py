from abc import ABC, abstractmethod

import whisper
from typing import Optional
import tempfile


class ISpeechRecognition(ABC):

    @abstractmethod
    async def transcribe(self, file: bytes) -> Optional[str]:
        pass