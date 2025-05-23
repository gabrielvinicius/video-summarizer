from sqlalchemy.orm import Session
from src.auth.domain.user import User
from typing import Optional


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, user: User) -> User:
        """Salva usuário no banco de dados."""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def find_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email."""
        return self.db.query(User).filter(User.email == email).first()

    def find_by_id(self, user_id: str) -> Optional[User]:
        """Busca usuário por ID."""
        return self.db.query(User).filter(User.id == user_id).first()
