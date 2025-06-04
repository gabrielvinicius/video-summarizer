import numpy as np
from typing import Optional, Tuple
import asyncio
import logging
from faster_whisper import WhisperModel

from src.transcription.infrastructure.speech_recognition import ISpeechRecognition

logger = logging.getLogger(__name__)


class FastWhisperTranscriber(ISpeechRecognition):
    def __init__(
            self,
            model_size: str = "base",
            device: str = "cpu",
            compute_type: str = "int8",
            language: Optional[str] = "pt",
    ):
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        self.language = language
        self.sample_rate = 16000

    async def transcribe(self, file: bytes) -> Optional[str]:
        try:
            audio_array, sample_rate = await self._decode_audio_bytes(file)
            return await self._transcribe_audio(audio_array, sample_rate)
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Transcription error: {str(e)}")

    async def _transcribe_audio(self, audio: np.ndarray, sample_rate: int) -> str:
        loop = asyncio.get_running_loop()

        # Executa o reconhecimento em thread separada
        segments, _ = await loop.run_in_executor(
            None,
            self.model.transcribe,
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            sample_rate=sample_rate
        )

        # Combina todos os segmentos de texto
        return " ".join(segment.text for segment in segments)

    async def _decode_audio_bytes(self, file_bytes: bytes) -> Tuple[np.ndarray, int]:
        """Decodifica bytes de áudio para array numpy usando FFmpeg"""
        command = [
            'ffmpeg',
            '-i', 'pipe:0',  # Entrada via stdin
            '-f', 's16le',  # Formato de saída: PCM signed 16-bit little-endian
            '-ac', '1',  # Canal único (mono)
            '-ar', str(self.sample_rate),  # Taxa de amostragem
            '-loglevel', 'error',  # Somente erros
            '-hide_banner',  # Oculta informações do banner
            'pipe:1'  # Saída via stdout
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

        # Converte bytes para array numpy int16
        audio_array = np.frombuffer(stdout, dtype=np.int16)
        return audio_array, self.sample_rate