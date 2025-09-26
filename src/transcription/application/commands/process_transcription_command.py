# src/transcription/application/commands/process_transcription_command.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessTranscriptionCommand:
    video_id: str
    provider: str
    language: str
