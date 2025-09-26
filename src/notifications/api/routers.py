# src/notifications/api/routers.py
from fastapi import APIRouter, Depends, HTTPException, status

# Import security and CQRS dependencies
from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
from src.shared.dependencies import get_notification_service, get_notification_queries
from src.notifications.application.notification_service import NotificationService
from src.notifications.application.queries.notification_queries import NotificationQueries
from .schemas import NotificationResponse, NotificationRequest

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_202_ACCEPTED, summary="Send a notification")
async def send_notification(
    request: NotificationRequest,
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user), # Ensure user is authenticated
):
    """Sends a notification to a user. Requires authentication."""
    # Authorization: Ensure a user can only send notifications on their own behalf (or is an admin)
    if str(request.user_id) != str(current_user.id) and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send notification for this user")

    try:
        notification = await service.send_notification(
            user_id=str(request.user_id),
            message=request.message,
            notification_type=request.type
        )
        return notification
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{notification_id}", response_model=NotificationResponse, summary="Get a notification by its ID")
async def get_notification_by_id(
    notification_id: str, 
    queries: NotificationQueries = Depends(get_notification_queries),
    current_user: User = Depends(get_current_user), # Ensure user is authenticated
):
    """Retrieves a notification by its ID."""
    notification = await queries.get_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Authorization: Ensure the user owns the notification or is an admin
    if str(notification.user_id) != str(current_user.id) and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this notification")

    return notification
