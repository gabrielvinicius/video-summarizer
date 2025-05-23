# auth/infrastructure/dependencies.py
from fastapi import Depends
from src.auth.application.auth_service import AuthService
from src.auth.infrastructure.user_repository import UserRepository
from src.shared.infrastructure.database import get_db


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repository = UserRepository(db)
    return AuthService(user_repository)
