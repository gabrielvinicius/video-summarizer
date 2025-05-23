from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    id: str  # UUID
    email: str  # Email único
    password_hash: str  # Hash bcrypt
    is_active: bool = True
    roles: List[UserRole] = [UserRole.USER]

    def has_role(self, role: UserRole) -> bool:
        return role in self.roles
