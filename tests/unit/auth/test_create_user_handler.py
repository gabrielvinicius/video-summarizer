# tests/unit/auth/test_create_user_handler.py
import pytest
from unittest.mock import AsyncMock

from src.auth.application.commands.create_user_command import CreateUserCommand
from src.auth.application.commands.create_user_command_handler import CreateUserCommandHandler
from src.auth.domain.user import User


@pytest.fixture
def user_repository():
    return AsyncMock()


@pytest.mark.asyncio
async def test_create_user_success(user_repository):
    """Tests successful user creation."""
    # Arrange
    user_repository.find_by_email.return_value = None
    user_repository.save.return_value = User(id="user1", email="test@example.com")
    
    handler = CreateUserCommandHandler(user_repository=user_repository)
    command = CreateUserCommand(email="test@example.com", password="password123")

    # Act
    result = await handler.handle(command)

    # Assert
    assert result.email == command.email
    user_repository.find_by_email.assert_awaited_once_with(command.email)
    user_repository.save.assert_awaited_once()
    # Check that the password was hashed
    saved_user = user_repository.save.await_args.args[0]
    assert saved_user.password_hash != command.password


@pytest.mark.asyncio
async def test_create_user_email_already_exists(user_repository):
    """Tests that an error is raised if the email already exists."""
    # Arrange
    user_repository.find_by_email.return_value = User(id="user1", email="test@example.com")
    
    handler = CreateUserCommandHandler(user_repository=user_repository)
    command = CreateUserCommand(email="test@example.com", password="password123")

    # Act & Assert
    with pytest.raises(ValueError, match="Email already registered"):
        await handler.handle(command)
    
    user_repository.save.assert_not_awaited()
