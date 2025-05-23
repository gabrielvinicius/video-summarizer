from fastapi import APIRouter, Depends

from src.notifications.api.schemas import NotificationResponse
from src.notifications.application.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: str, service: NotificationService = Depends()):
    return service.notification_repo.find_by_id(notification_id)
