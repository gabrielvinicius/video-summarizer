# auth/infrastructure/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session

from src.auth.application.auth_service import AuthService
from src.shared.dependencies import get_user_repository
from src.auth.infrastructure.user_repository import UserRepository


def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repository)
