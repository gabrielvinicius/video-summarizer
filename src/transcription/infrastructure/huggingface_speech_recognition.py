import io
import os
import tempfile
from typing import Optional

import av
import numpy as np
import resampy
from transformers import pipeline
import logging

from src.transcription.infrastructure.speech_recognition import ISpeechRecognition

logger = logging.getLogger(__name__)


class HuggingfaceTranscriber(ISpeechRecognition):
    def __init__(self, model_name: str = "openai/whisper-base"):
        self.model = pipeline(task="automatic-speech-recognition",model=model_name)
        self.sample_rate = 16000  # Whisper expects 16kHz audio

    async def transcribe(self, file: bytes) -> Optional[str]:
        path = None
        try:
            path = await self._decode_file_bytes(file)
            # audio = whisper.load_audio(path)

            # audio = await self._decode_audio_bytes(file)

            # Ensure length compatibility with Whisper
            # audio = whisper.pad_or_trim(audio)

            # Generate mel spectrogram and transcribe
            # mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            # options = whisper.DecodingOptions(fp16=False)
            # result = whisper.decode(self.model, mel, options)
            result = self.model(path)

            return result["text"]
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise RuntimeError(f"Transcription error: {str(e)}")
        finally:
            os.unlink(path)

    async def _decode_audio_bytes(self, file_bytes: bytes) -> np.ndarray:
        """Decodes audio or audio-track-from-video to float32 mono 16kHz"""
        try:
            buffer = io.BytesIO(file_bytes)
            container = av.open(buffer)

            audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
            if audio_stream is None:
                raise ValueError("No audio stream found in the input file")

            frames = []
            for packet in container.demux(audio_stream):
                for frame in packet.decode():
                    samples = frame.to_ndarray()
                    if samples.ndim > 1:
                        samples = np.mean(samples, axis=0)  # Convert to mono
                    frames.append(samples)

            if not frames:
                raise ValueError("No audio frames found")

            audio = np.concatenate(frames).astype(np.float32)
            original_rate = audio_stream.rate

            if original_rate != self.sample_rate:
                audio = resampy.resample(audio, original_rate, self.sample_rate)

            audio /= np.max(np.abs(audio)) + 1e-9  # Normalize

            return audio

        except Exception as e:
            logger.error(f"Audio decoding from video/audio failed: {str(e)}")
            raise RuntimeError(f"Audio decoding error: {str(e)}")

    async def _decode_file_bytes(self, file_bytes: bytes) -> str:
        tmp = tempfile.NamedTemporaryFile(suffix=".tmp", delete=False)
        tmp.write(file_bytes)
        tmp.flush()
        tmp.close()
        return tmp.name
