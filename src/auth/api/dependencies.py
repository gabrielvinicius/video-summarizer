# src/auth/api/dependencies.py
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from jose import JWTError

from src.auth.domain.user import User, UserRole
from src.auth.utils.token import verify_token
from src.auth.infrastructure.user_repository import UserRepository
from src.auth.application.auth_service import AuthService
from src.shared.dependencies import get_user_repository

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repository=user_repository)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = await user_repo.find_by_id(UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuário inativo ou inexistente")

    return user



async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
