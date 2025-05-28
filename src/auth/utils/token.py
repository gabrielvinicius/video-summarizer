from datetime import datetime, timedelta
from jose import jwt, JWTError
from uuid import UUID
from typing import Optional
from src.auth.domain.user import User, UserRole
from src.shared.config.auth_settings import AuthSettings

settings = AuthSettings()


def create_access_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "exp": expire
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
