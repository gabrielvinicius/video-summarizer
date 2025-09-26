# tests/unit/auth/test_authenticate_user_command_handler.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.auth.application.commands.authenticate_user_command import AuthenticateUserCommand
from src.auth.application.commands.authenticate_user_command_handler import AuthenticateUserCommandHandler
from src.auth.domain.user import User
from src.auth.config.settings import AuthSettings


@pytest.fixture
def user_repository():
    return AsyncMock()


@pytest.fixture
def auth_settings():
    return AuthSettings(secret_key="test-secret", algorithm="HS256", access_token_expire_minutes=30)


@pytest.mark.asyncio
@patch("src.auth.application.commands.authenticate_user_command_handler.pwd_context")
@patch("src.auth.application.commands.authenticate_user_command_handler.create_access_token")
async def test_authenticate_user_success(mock_create_token, mock_pwd_context, user_repository, auth_settings):
    """Tests successful user authentication and token generation."""
    # Arrange
    mock_pwd_context.verify.return_value = True
    mock_create_token.return_value = "fake-jwt-token"
    user = User(id="user1", email="test@example.com", password_hash="hashed_password")
    user_repository.find_by_email.return_value = user

    handler = AuthenticateUserCommandHandler(user_repository=user_repository, settings=auth_settings)
    command = AuthenticateUserCommand(email="test@example.com", password="password123")

    # Act
    token = await handler.handle(command)

    # Assert
    assert token == "fake-jwt-token"
    user_repository.find_by_email.assert_awaited_once_with(command.email)
    mock_pwd_context.verify.assert_called_once_with(command.password, user.password_hash)
    mock_create_token.assert_called_once_with(user.id)


@pytest.mark.asyncio
@patch("src.auth.application.commands.authenticate_user_command_handler.pwd_context")
async def test_authenticate_user_wrong_password(mock_pwd_context, user_repository, auth_settings):
    """Tests that authentication fails with an incorrect password."""
    # Arrange
    mock_pwd_context.verify.return_value = False
    user = User(id="user1", email="test@example.com", password_hash="hashed_password")
    user_repository.find_by_email.return_value = user

    handler = AuthenticateUserCommandHandler(user_repository=user_repository, settings=auth_settings)
    command = AuthenticateUserCommand(email="test@example.com", password="wrong_password")

    # Act
    token = await handler.handle(command)

    # Assert
    assert token is None


@pytest.mark.asyncio
async def test_authenticate_user_not_found(user_repository, auth_settings):
    """Tests that authentication fails if the user is not found."""
    # Arrange
    user_repository.find_by_email.return_value = None

    handler = AuthenticateUserCommandHandler(user_repository=user_repository, settings=auth_settings)
    command = AuthenticateUserCommand(email="notfound@example.com", password="password123")

    # Act
    token = await handler.handle(command)

    # Assert
    assert token is None
