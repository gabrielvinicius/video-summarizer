# tests/unit/notification/test_send_notification_handler.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.auth.domain.user import User
from src.notifications.application.commands.send_notification_command import SendNotificationCommand
from src.notifications.application.commands.send_notification_command_handler import SendNotificationCommandHandler
from src.notifications.domain.notification import NotificationType, NotificationStatus

@pytest.fixture
def handler_mocks():
    """Sets up mocks for the SendNotificationCommandHandler dependencies."""
    return {
        "email_adapter": AsyncMock(),
        "sms_adapter": AsyncMock(),
        "webhook_adapter": AsyncMock(),
        "notification_repository": AsyncMock(),
        "user_repository": AsyncMock(),
    }

@pytest.mark.asyncio
async def test_send_email_notification_success(handler_mocks):
    """Tests successful sending of an email notification."""
    # Arrange
    user_id = str(uuid4())
    user = User(id=user_id, email="test@example.com")
    handler_mocks["user_repository"].find_by_id.return_value = user

    handler = SendNotificationCommandHandler(**handler_mocks)
    command = SendNotificationCommand(user_id=user_id, message="Test message", notification_type=NotificationType.EMAIL)

    # Act
    result = await handler.handle(command)

    # Assert
    assert result.status == NotificationStatus.SENT
    handler_mocks["email_adapter"].send.assert_awaited_once_with(user.email, "Notification", command.message)
    handler_mocks["notification_repository"].save.assert_awaited()

@pytest.mark.asyncio
async def test_send_notification_user_not_found(handler_mocks):
    """Tests that an error is raised if the user is not found."""
    # Arrange
    handler_mocks["user_repository"].find_by_id.return_value = None
    handler = SendNotificationCommandHandler(**handler_mocks)
    command = SendNotificationCommand(user_id="non-existent-user", message="Test", notification_type=NotificationType.EMAIL)

    # Act & Assert
    with pytest.raises(ValueError, match="User not found"):
        await handler.handle(command)
    handler_mocks["notification_repository"].save.assert_not_awaited()

@pytest.mark.asyncio
async def test_send_notification_adapter_fails(handler_mocks):
    """Tests that the notification status is marked as FAILED if the adapter fails."""
    # Arrange
    user_id = str(uuid4())
    user = User(id=user_id, email="test@example.com")
    handler_mocks["user_repository"].find_by_id.return_value = user
    handler_mocks["email_adapter"].send.side_effect = Exception("SMTP server down")

    handler = SendNotificationCommandHandler(**handler_mocks)
    command = SendNotificationCommand(user_id=user_id, message="Test message", notification_type=NotificationType.EMAIL)

    # Act
    result = await handler.handle(command)

    # Assert
    assert result.status == NotificationStatus.FAILED
    assert "SMTP server down" in result.error_message
    handler_mocks["notification_repository"].save.assert_awaited()
