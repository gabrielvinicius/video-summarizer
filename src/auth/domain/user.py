from enum import Enum
from typing import List

from sqlalchemy import Column, String, Boolean, Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from src.shared.infrastructure.database import Base
import uuid

#from src.video_management.domain.video import Video


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(SQLAEnum(UserRole, name="user_role_enum"), default=UserRole.USER, nullable=False)
    videos: Mapped[List["Video"]] = relationship(back_populates="user")