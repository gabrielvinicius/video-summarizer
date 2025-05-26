from sqlalchemy.orm import Session
from src.transcription.domain.transcription import Transcription


class TranscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, transcription_id: str) -> Transcription | None:
        return self.db.query(Transcription).filter(Transcription.id == transcription_id).first()

    def save(self, transcription: Transcription) -> Transcription:
        self.db.add(transcription)
        self.db.commit()
        self.db.refresh(transcription)
        return transcription

    def list_by_user(self, user_id: str) -> list[Transcription]:
        return self.db.query(Transcription).filter(Transcription.user_id == user_id).all()

    def delete(self, transcription_id: str) -> bool:
        transcription = self.find_by_id(transcription_id)
        if transcription:
            self.db.delete(transcription)
            self.db.commit()
            return True
        return False
