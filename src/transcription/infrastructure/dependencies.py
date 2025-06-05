from src.transcription.infrastructure.speech_recognition import ISpeechRecognition
from .whisper_speech_recognition import WhisperTranscriber


def get_speech_recognition() -> ISpeechRecognition:
    return WhisperTranscriber()
