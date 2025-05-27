from datetime import datetime, timedelta
from uuid import UUID

from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional
from src.auth.domain.user import User, UserRole
from src.shared.config.auth_settings import AuthSettings
from src.shared.utils.id_generator import generate_id
from src.auth.infrastructure.user_repository import UserRepository

# from src.shared.utils.id_generator import generate_id


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = AuthSettings()


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    async def create_user(self, email: str, password: str) -> User:
        """Cria um novo usuário com senha hasheada."""
        if await self.user_repository.find_by_email(email):
            raise ValueError("Email já registrado")

        hashed_password = pwd_context.hash(password)
        user = User(id=generate_id(),
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
        expires = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": user.email,
            "id": str(user.id),
            "role": user.role.value,  # 👈 agora só um role
            "exp": expires
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    @staticmethod
    def verify_token(token: str) -> Optional[User]:
        """Decodifica e valida um JWT token."""
        from src.shared.dependencies import get_user_repository
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=settings.algorithm)
            # user: User = get_user_repository().find_by_id(UUID(payload["id"]))
            # return user
            return User(
                id=UUID(payload["id"]),
                email=payload["sub"],
                role=UserRole(payload["role"]),
                is_active=True
            )
        except JWTError:
            return None
