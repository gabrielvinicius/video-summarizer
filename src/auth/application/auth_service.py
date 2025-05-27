from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional
from src.auth.domain.user import User, UserRole
from src.shared.config.auth_settings import AuthSettings
from src.shared.utils.id_generator import generate_id

# from src.shared.utils.id_generator import generate_id


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = AuthSettings()


class AuthService:
    def __init__(self, user_repository):
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
            roles=[UserRole.USER]
        )
        return self.user_repository.save(user)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Verifica credenciais e retorna o usuário se válido."""
        user = self.user_repository.find_by_email(email)
        if not user or not pwd_context.verify(password, user.password_hash):
            return None
        return user

    def create_access_token(self, user: User) -> str:
        """Gera JWT token para o usuário."""
        expires = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": user.email,
            "id": user.id,
            "roles": [role.value for role in user.roles],
            "exp": expires
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    @staticmethod
    def verify_token(token: str) -> Optional[User]:
        """Decodifica e valida um JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=settings.algorithm)
            return User(
                id=payload["id"],
                email=payload["sub"],
                roles=[UserRole(role) for role in payload["roles"]]
            )
        except JWTError:
            return None
