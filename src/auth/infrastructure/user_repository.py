from uuid import UUID
from typing import Optional, Sequence, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from src.auth.domain.user import User
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, db: Union[AsyncSession, Session]):
        self.db = db

    def _is_async(self):
        return isinstance(self.db, AsyncSession)

    async def save(self, user: User) -> User:
        """Saves a user to the database."""
        self.db.add(user)
        try:
            if self._is_async():
                await self.db.commit()
                await self.db.refresh(user)
            else:
                self.db.commit()
                self.db.refresh(user)
            return user
        except Exception as e:
            if self._is_async():
                await self.db.rollback()
            else:
                self.db.rollback()
            logger.error(f"Error saving user {getattr(user, 'id', None)}: {e}")
            raise

    async def find_by_email(self, email: str) -> Optional[User]:
        """Finds a user by email."""
        stmt = select(User).where(User.email == email)
        if self._is_async():
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        else:
            result = self.db.execute(stmt)
            return result.scalar_one_or_none()

    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """Finds a user by ID."""
        stmt = select(User).where(User.id == user_id)
        if self._is_async():
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        else:
            result = self.db.execute(stmt)
            return result.scalar_one_or_none()

    async def delete(self, user_id: UUID) -> bool:
        """Deletes a user by ID. Returns True if deleted, False if not found."""
        stmt = delete(User).where(User.id == user_id).returning(User.id)
        try:
            if self._is_async():
                result = await self.db.execute(stmt)
                await self.db.commit()
                deleted_id = result.scalar()
            else:
                result = self.db.execute(stmt)
                self.db.commit()
                deleted_id = result.scalar()
            return deleted_id is not None
        except Exception as e:
            if self._is_async():
                await self.db.rollback()
            else:
                self.db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            raise

    async def list_all(self) -> Sequence[User]:
        """Returns all users."""
        stmt = select(User)
        if self._is_async():
            result = await self.db.execute(stmt)
            return result.scalars().all()
        else:
            result = self.db.execute(stmt)
            return result.scalars().all()
