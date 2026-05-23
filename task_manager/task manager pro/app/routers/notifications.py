"""Notification endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from .. import crud_pro
from ..database_pro import get_db
from ..schemas_pro import NotificationResponse

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List notifications for the current user."""
    return crud_pro.get_notifications(db, current_user, unread_only=unread_only)


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    success = crud_pro.mark_notification_read(db, notification_id, current_user)
    if not success:
        return {"marked": False}
    return {"marked": True}


@router.patch("/{notification_id}/retry")
async def retry_failed_notification(
    notification_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retry a failed notification delivery."""
    notification = crud_pro.retry_notification(db, notification_id, current_user)
    if not notification:
        return {"retried": False}
    return {"retried": True, "delivery_status": notification.delivery_status}
