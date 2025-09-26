# src/auth/application/auth_service.py
from typing import Optional

from src.auth.domain.user import User
# Import the new CQRS components
from .commands.create_user_command import CreateUserCommand
from .commands.create_user_command_handler import CreateUserCommandHandler
from .commands.authenticate_user_command import AuthenticateUserCommand
from .commands.authenticate_user_command_handler import AuthenticateUserCommandHandler


class AuthService:
    """Facade service to dispatch authentication commands."""
    def __init__(
        self,
        create_user_handler: CreateUserCommandHandler,
        authenticate_user_handler: AuthenticateUserCommandHandler,
    ):
        self.create_user_handler = create_user_handler
        self.authenticate_user_handler = authenticate_user_handler

    async def create_user(self, email: str, password: str) -> User:
        """Dispatches the CreateUserCommand."""
        command = CreateUserCommand(email=email, password=password)
        return await self.create_user_handler.handle(command)

    async def authenticate_user_and_get_token(self, email: str, password: str) -> Optional[str]:
        """Dispatches the AuthenticateUserCommand and returns a token."""
        command = AuthenticateUserCommand(email=email, password=password)
        return await self.authenticate_user_handler.handle(command)
