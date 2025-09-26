import numpy as np
from typing import Optional, Tuple
import asyncio
import logging
from faster_whisper import WhisperModel

from src.transcription.infrastructure.interfaces import ISpeechRecognition
from src.transcription.infrastructure.dependencies import register_speech_recognition

logger = logging.getLogger(__name__)


@register_speech_recognition("fastwhisper")
class FastWhisperTranscriber(ISpeechRecognition):
    def __init__(
            self,
            model_size: str = "base",
            device: str = "cpu",
            compute_type: str = "int8",
            language: Optional[str] = "en",
    ):
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        self.language = language
        self.sample_rate = 16000

    @property
    def provider_name(self) -> str:
        return "fastwhisper"

    async def transcribe(self, file: bytes, language: str = "en") -> Optional[str]:
        try:
            # The language passed as an argument takes precedence over the instance's default language
            lang_to_use = language if language else self.language
            audio_array, _ = await self._decode_audio_bytes(file)
            return await self._transcribe_audio(audio_array, lang_to_use)
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Transcription error: {str(e)}")

    async def _transcribe_audio(self, audio: np.ndarray, language: str) -> str:
        loop = asyncio.get_running_loop()

        # Run recognition in a separate thread
        segments, _ = await loop.run_in_executor(
            None,
            self.model.transcribe,
            audio,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        # Combine all text segments
        return " ".join(segment.text for segment in segments)

    async def _decode_audio_bytes(self, file_bytes: bytes) -> Tuple[np.ndarray, int]:
        """Decodes audio bytes to a numpy array using FFmpeg."""
        command = [
            'ffmpeg',
            '-i', 'pipe:0',  # Input from stdin
            '-f', 's16le',  # Output format: PCM signed 16-bit little-endian
            '-ac', '1',  # Single channel (mono)
            '-ar', str(self.sample_rate),  # Sample rate
            '-loglevel', 'error',  # Only log errors
            '-hide_banner',  # Hide banner info
            'pipe:1'  # Output to stdout
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate(input=file_bytes)
        await process.wait()

        if process.returncode != 0:
            err_msg = stderr.decode().strip() if stderr else f"FFmpeg error {process.returncode}"
            raise RuntimeError(f"Audio decoding failed: {err_msg}")

        # Convert bytes to numpy int16 array
        audio_array = np.frombuffer(stdout, dtype=np.int16)
        return audio_array, self.sample_rate
