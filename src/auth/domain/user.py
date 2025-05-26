import uuid

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    id: str = uuid.uuid4()
    email: EmailStr  # Email único
    password_hash: str  # Hash bcrypt
    is_active: bool = True
    roles: List[UserRole] = [UserRole.USER]
    videos: List[int] = None

    def has_role(self, role: UserRole) -> bool:
        return role in self.roles

    class Config:
        orm_mode = True