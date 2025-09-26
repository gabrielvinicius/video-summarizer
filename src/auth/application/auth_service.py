from uuid import UUID
from passlib.context import CryptContext
from typing import Optional, Sequence

from src.auth.config.settings import AuthSettings
from src.auth.domain.user import User, UserRole
from src.auth.infrastructure.user_repository import UserRepository
from src.auth.utils.token import create_access_token as token_util_create, verify_token as token_util_verify
from src.shared.utils.id_generator import generate_id

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = AuthSettings()


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    async def create_user(self, email: str, password: str) -> User:
        """Creates a new user with a hashed password."""
        if await self.user_repository.find_by_email(email):
            raise ValueError("Email already registered")

        hashed_password = pwd_context.hash(password)
        user = User(
            id=generate_id(),
            email=email,
            password_hash=hashed_password,
            role=UserRole.USER
        )
        return await self.user_repository.save(user)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.user_repository.find_by_email(email)
        if not user or not pwd_context.verify(password, user.password_hash):
            return None
        return user

    def create_access_token(self, user: User) -> str:
        return token_util_create(user.id)

    def verify_token(self, token: str) -> Optional[User]:
        return token_util_verify(token)

    async def get_user_by_id(self, user_uuid: str) -> User:
        return await self.user_repository.find_by_id(UUID(user_uuid))

    async def list_all_users(self) -> Sequence[User]:
        """Lists all users."""
        return await self.user_repository.list_all()
