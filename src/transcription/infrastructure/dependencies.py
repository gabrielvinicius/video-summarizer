from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from .whisper_speech_recognition import WhisperTranscriber

async def get_speech_recognition() -> ISpeechRecognition:
    return WhisperTranscriber()