from fastapi import APIRouter, Depends, HTTPException

from src.notifications.api.schemas import NotificationResponse
from src.notifications.application.notification_service import NotificationService
from src.shared.dependencies import get_notification_service # Correct dependency import

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification_by_id(
    notification_id: str, 
    service: NotificationService = Depends(get_notification_service) # Use the correct dependency getter
):
    """Retrieves a notification by its ID."""
    notification = await service.get_notification_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification
