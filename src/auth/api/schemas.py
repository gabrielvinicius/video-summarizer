from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool

    model_config = {
        "from_attributes": True  # ✅ novo
    }


class LoginJSON(BaseModel):
    username: str
    password: str
