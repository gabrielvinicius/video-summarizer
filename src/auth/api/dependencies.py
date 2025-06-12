from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from jose import JWTError

from src.auth.domain.user import User, UserRole
from src.auth.utils.token import verify_token
from src.auth.infrastructure.user_repository import UserRepository
from src.auth.application.auth_service import AuthService
from src.shared.dependencies import get_auth_service

# OAuth2 scheme - corrigido para usar a URL completa
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        auth_service: AuthService = Depends(get_auth_service)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token)
        if not payload:
            raise credentials_exception

        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception

        # Validação adicional do formato UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise credentials_exception

        user = await auth_service.get_user_by_id(str(user_uuid))

        if not user or not user.is_active:
            raise credentials_exception

        return user

    except JWTError as e:
        raise credentials_exception from e


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


# Nova dependência para usuários comuns (não-admin)
async def get_current_active_user(
        current_user: User = Depends(get_current_user),
) -> User:
    return current_user