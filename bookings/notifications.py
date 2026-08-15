from .models import Notification


def create_notification(
    recipient,
    message,
    notification_type,
    booking=None
):
    return Notification.objects.create(
        recipient=recipient,
        booking=booking,
        notification_type=notification_type,
        message=message,
    )