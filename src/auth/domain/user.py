from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    id: int | None = None
    email: EmailStr  # Email único
    password_hash: str  # Hash bcrypt
    is_active: bool = True
    roles: List[UserRole] = [UserRole.USER]

    def has_role(self, role: UserRole) -> bool:
        return role in self.roles

    class Config:
        orm_mode = True