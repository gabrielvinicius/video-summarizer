# src/auth/bootstrap.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.auth.application.auth_service import AuthService
from src.auth.application.commands.create_user_command_handler import CreateUserCommandHandler
from src.auth.application.commands.authenticate_user_command_handler import AuthenticateUserCommandHandler
from src.auth.application.queries.auth_queries import AuthQueries
from src.auth.config.settings import AuthSettings
from src.auth.infrastructure.user_repository import UserRepository

def bootstrap_auth_module(db_session: AsyncSession) -> Dict[str, Any]:
    """Constructs and returns the services for the auth module."""
    # This function is now the single source of truth for constructing the auth module.
    user_repository = UserRepository(db=db_session)
    auth_settings = AuthSettings()

    create_user_handler = CreateUserCommandHandler(user_repository=user_repository)
    authenticate_user_handler = AuthenticateUserCommandHandler(
        user_repository=user_repository, 
        settings=auth_settings
    )

    auth_service = AuthService(
        create_user_handler=create_user_handler,
        authenticate_user_handler=authenticate_user_handler
    )
    auth_queries = AuthQueries(user_repository=user_repository)

    return {
        "user_repository": user_repository,
        "auth_service": auth_service,
        "auth_queries": auth_queries,
    }
