import pytest
from unittest.mock import AsyncMock, MagicMock
from src.notifications.application.notification_service import NotificationService


@pytest.mark.asyncio
async def test_send_email_notification():
    mock_email = AsyncMock()
    mock_user_repo = MagicMock(find_by_id=MagicMock(return_value=User(email="test@test.com")))
    mock_notification_repo = MagicMock()

    service = NotificationService(
        email_adapter=mock_email,
        sms_adapter=MagicMock(),
        webhook_adapter=MagicMock(),
        notification_repository=mock_notification_repo,
        user_repository=mock_user_repo
    )

    notification = await service.send_notification("user-123", "Teste", "EMAIL")
    assert notification.status == "SENT"
    mock_email.send.assert_awaited_once()
