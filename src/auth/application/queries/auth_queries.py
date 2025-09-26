# src/auth/application/queries/auth_queries.py
from typing import Optional, Sequence
from uuid import UUID

from src.auth.domain.user import User
from src.auth.infrastructure.user_repository import UserRepository


class AuthQueries:
    """Handles all read-only operations for users."""
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieves a user by their unique ID."""
        return await self.user_repository.find_by_id(UUID(user_id))

    async def list_all(self) -> Sequence[User]:
        """Lists all users."""
        return await self.user_repository.list_all()
