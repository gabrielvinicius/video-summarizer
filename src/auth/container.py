# src/auth/container.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.application.auth_service import AuthService
from src.auth.application.commands.create_user_command_handler import CreateUserCommandHandler
from src.auth.application.commands.authenticate_user_command_handler import AuthenticateUserCommandHandler
from src.auth.application.queries.auth_queries import AuthQueries
from src.auth.config.settings import AuthSettings
from src.auth.infrastructure.user_repository import UserRepository


class AuthContainer:
    """Container for the authentication module's dependencies."""
    def __init__(self, db_session: AsyncSession):
        self.settings = AuthSettings()
        self.user_repository = UserRepository(db=db_session)

        # Create Command Handlers
        create_user_handler = CreateUserCommandHandler(user_repository=self.user_repository)
        authenticate_user_handler = AuthenticateUserCommandHandler(
            user_repository=self.user_repository, 
            settings=self.settings
        )

        # Create Facade Service (for commands)
        self.service = AuthService(
            create_user_handler=create_user_handler,
            authenticate_user_handler=authenticate_user_handler
        )

        # Create Query Service
        self.queries = AuthQueries(user_repository=self.user_repository)
