# src/auth/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Annotated

from pydantic import BaseSettings

from src.auth.application.auth_service import AuthService
from src.auth.infrastructure.user_repository import UserRepository
from src.shared.infrastructure.database import get_db
from sqlalchemy.orm import Session

# Configuração do esquema OAuth2 para token JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class AuthSettings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    settings = AuthSettings()
    user_repository = UserRepository(db)
    return AuthService(
        user_repository=user_repository,
        secret_key=settings.secret_key,  # Agora seguro!
        algorithm=settings.algorithm
    )


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Valida o token JWT e retorna o usuário autenticado."""
    try:
        user = auth_service.verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais",
            headers={"WWW-Authenticate": "Bearer"},
        )
