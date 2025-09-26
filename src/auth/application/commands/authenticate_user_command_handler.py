# src/auth/application/commands/authenticate_user_command_handler.py
from typing import Optional
from passlib.context import CryptContext

from src.auth.config.settings import AuthSettings
from src.auth.infrastructure.user_repository import UserRepository
from src.auth.utils.token import create_access_token
from .authenticate_user_command import AuthenticateUserCommand

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticateUserCommandHandler:
    def __init__(self, user_repository: UserRepository, settings: AuthSettings):
        self.user_repository = user_repository
        self.settings = settings

    async def handle(self, command: AuthenticateUserCommand) -> Optional[str]:
        """Handles user authentication and token creation."""
        user = await self.user_repository.find_by_email(command.email)
        if not user or not pwd_context.verify(command.password, user.password_hash):
            return None
        
        token = create_access_token(user.id)
        return token
