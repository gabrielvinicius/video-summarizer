# tests/unit/notification/test_notification_service.py
import pytest
from unittest.mock import AsyncMock

from src.notifications.application.notification_service import NotificationService
from src.notifications.application.commands.send_notification_command import SendNotificationCommand
from src.notifications.domain.notification import NotificationType


@pytest.fixture
def mock_send_notification_handler():
    return AsyncMock()


@pytest.mark.asyncio
async def test_send_notification_dispatches_command(mock_send_notification_handler):
    """Tests that the NotificationService facade correctly dispatches the SendNotificationCommand."""
    # Arrange
    service = NotificationService(send_notification_handler=mock_send_notification_handler)
    user_id = "user1"
    message = "Test message"
    notification_type = NotificationType.EMAIL

    # Act
    await service.send_notification(user_id, message, notification_type)

    # Assert
    mock_send_notification_handler.handle.assert_awaited_once()
    dispatched_command = mock_send_notification_handler.handle.await_args.args[0]
    assert isinstance(dispatched_command, SendNotificationCommand)
    assert dispatched_command.user_id == user_id
    assert dispatched_command.message == message
    assert dispatched_command.notification_type == notification_type
