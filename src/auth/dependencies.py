# src/auth/dependencies.py
from sqlalchemy.ext.asyncio import AsyncSession
from .container import AuthContainer

def bootstrap_auth_module(db_session: AsyncSession) -> AuthContainer:
    """Initializes and returns the container for the auth module."""
    return AuthContainer(db_session=db_session)
