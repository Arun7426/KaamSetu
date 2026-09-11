from datetime import timedelta

from django.utils import timezone

from .models import Booking
from .notifications import create_notification


BOOKING_REQUEST_TIMEOUT = timedelta(hours=1)


def expire_pending_bookings():
    """
    Automatically cancel pending booking requests
    that have been waiting for more than 1 hour.
    """

    cutoff = timezone.now() - BOOKING_REQUEST_TIMEOUT

    expired_bookings = Booking.objects.select_related(
        "worker",
        "customer",
    ).filter(
        status="Pending",
        created_at__lte=cutoff,
    )

    expired_count = 0

    for booking in expired_bookings:
        booking.status = "Cancelled"
        booking.save(update_fields=["status"])

        # Notify customer
        if booking.customer_id:
            create_notification(
                recipient=booking.customer,
                booking=booking,
                notification_type="rejected",
                message=(
                    f"{booking.worker.name} did not respond to your booking "
                    "request within 1 hour. The request has been "
                    "automatically cancelled."
                ),
            )

        # Notify worker if a user account is linked
        if getattr(booking.worker, "user_id", None):
            create_notification(
                recipient=booking.worker.user,
                booking=booking,
                notification_type="rejected",
                message=(
                    "This booking request expired because it was not "
                    "accepted within 1 hour."
                ),
            )

        expired_count += 1

    return expired_count