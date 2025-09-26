# tests/unit/auth/test_auth_queries.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.auth.application.queries.auth_queries import AuthQueries
from src.auth.domain.user import User


@pytest.fixture
def user_repository():
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_by_id(user_repository):
    """Tests retrieving a user by their ID."""
    # Arrange
    user_id = uuid4()
    expected_user = User(id=user_id, email="test@example.com")
    user_repository.find_by_id.return_value = expected_user

    queries = AuthQueries(user_repository=user_repository)

    # Act
    result = await queries.get_by_id(str(user_id))

    # Assert
    assert result == expected_user
    user_repository.find_by_id.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_list_all(user_repository):
    """Tests listing all users."""
    # Arrange
    expected_users = [
        User(id=uuid4(), email="test1@example.com"),
        User(id=uuid4(), email="test2@example.com"),
    ]
    user_repository.list_all.return_value = expected_users

    queries = AuthQueries(user_repository=user_repository)

    # Act
    result = await queries.list_all()

    # Assert
    assert result == expected_users
    user_repository.list_all.assert_awaited_once()
