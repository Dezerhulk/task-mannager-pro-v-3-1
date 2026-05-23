"""Notification delivery helpers for webhook-based channels."""

import json
from urllib.request import Request, urlopen

from .config import settings
from .models_pro import Notification


def deliver_notification(notification: Notification) -> None:
    """Attempt to deliver a notification via its configured channel."""
    if notification.channel == "webhook":
        if not settings.notification_webhook_url:
            raise RuntimeError("notification_webhook_url is not configured")

        payload = {
            "id": notification.id,
            "type": notification.notification_type,
            "title": notification.title,
            "message": notification.message,
            "project_id": notification.project_id,
            "task_id": notification.task_id,
            "channel": notification.channel,
        }
        request = Request(
            settings.notification_webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError(f"Webhook returned status {response.status}")
        return

    raise RuntimeError(f"Unsupported notification channel: {notification.channel}")
