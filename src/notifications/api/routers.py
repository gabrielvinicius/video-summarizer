from fastapi import APIRouter, Depends, HTTPException, status

# Import the correct CQRS dependencies
from src.shared.dependencies import get_notification_service, get_notification_queries
from src.notifications.application.notification_service import NotificationService
from src.notifications.application.queries.notification_queries import NotificationQueries
from .schemas import NotificationResponse, NotificationRequest

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_notification(
    request: NotificationRequest,
    service: NotificationService = Depends(get_notification_service),
):
    """Sends a notification to a user."""
    try:
        notification = await service.send_notification(
            user_id=str(request.user_id),
            message=request.message,
            notification_type=request.type
        )
        return notification
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification_by_id(
    notification_id: str, 
    queries: NotificationQueries = Depends(get_notification_queries)
):
    """Retrieves a notification by its ID."""
    notification = await queries.get_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification
