# tests/unit/notification/test_notification_queries.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.notifications.application.queries.notification_queries import NotificationQueries
from src.notifications.domain.notification import Notification


@pytest.fixture
def mock_notification_repository():
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_by_id(mock_notification_repository):
    """Tests retrieving a notification by its ID."""
    # Arrange
    notification_id = str(uuid4())
    expected_notification = Notification(id=notification_id, user_id=str(uuid4()), content="Test")
    mock_notification_repository.find_by_id.return_value = expected_notification

    queries = NotificationQueries(notification_repository=mock_notification_repository)

    # Act
    result = await queries.get_by_id(notification_id)

    # Assert
    assert result == expected_notification
    mock_notification_repository.find_by_id.assert_awaited_once_with(notification_id)


@pytest.mark.asyncio
async def test_list_by_user(mock_notification_repository):
    """Tests listing notifications for a specific user."""
    # Arrange
    user_id = str(uuid4())
    expected_notifications = [
        Notification(id=str(uuid4()), user_id=user_id, content="Notification 1"),
        Notification(id=str(uuid4()), user_id=user_id, content="Notification 2"),
    ]
    mock_notification_repository.list_by_user.return_value = expected_notifications

    queries = NotificationQueries(notification_repository=mock_notification_repository)

    # Act
    result = await queries.list_by_user(user_id)

    # Assert
    assert result == expected_notifications
    mock_notification_repository.list_by_user.assert_awaited_once_with(user_id)
