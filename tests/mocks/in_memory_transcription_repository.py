# tests/mocks/in_memory_transcription_repository.py
from typing import Dict, Optional, List
from uuid import UUID

from src.transcription.domain.transcription import Transcription


class InMemoryTranscriptionRepository:
    def __init__(self):
        self.transcriptions: Dict[str, Transcription] = {}

    async def save(self, transcription: Transcription) -> Transcription:
        self.transcriptions[str(transcription.id)] = transcription
        return transcription

    async def find_by_id(self, transcription_id: str) -> Optional[Transcription]:
        return self.transcriptions.get(str(transcription_id))

    async def find_by_video_id(self, video_id: str) -> Optional[Transcription]:
        for trans in self.transcriptions.values():
            if str(trans.video_id) == str(video_id):
                return trans
        return None

    def clear(self):
        self.transcriptions.clear()
