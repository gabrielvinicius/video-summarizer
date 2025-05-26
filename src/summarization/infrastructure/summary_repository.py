from sqlalchemy.orm import Session
from src.summarization.domain.summary import Summary


class SummaryRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, summary_id: str) -> Summary | None:
        return self.db.query(Summary).filter(Summary.id == summary_id).first()

    def save(self, summary: Summary) -> Summary:
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary

    def list_by_user(self, user_id: str) -> list[Summary]:
        return self.db.query(Summary).filter(Summary.user_id == user_id).all()

    def delete(self, summary_id: str) -> bool:
        summary = self.find_by_id(summary_id)
        if summary:
            self.db.delete(summary)
            self.db.commit()
            return True
        return False
