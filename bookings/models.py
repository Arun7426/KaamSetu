from django.db import models
from workers.models import Worker


class Booking(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Accepted", "Accepted"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    worker = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    customer_name = models.CharField(max_length=100)

    customer_mobile = models.CharField(max_length=15)

    customer_address = models.TextField()

    work_date = models.DateField()

    work_description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.worker.name}"