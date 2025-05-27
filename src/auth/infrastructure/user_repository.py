from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.auth.domain.user import User
from typing import Optional


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, user: User) -> User:
        """Salva usuário no banco de dados."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """Busca usuário por ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
