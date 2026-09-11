from django.core.management.base import BaseCommand

from bookings.services import expire_pending_bookings


class Command(BaseCommand):
    help = "Automatically cancel pending booking requests older than 1 hour."

    def handle(self, *args, **options):
        expired_count = expire_pending_bookings()

        self.stdout.write(
            self.style.SUCCESS(
                f"{expired_count} pending booking(s) expired."
            )
        )