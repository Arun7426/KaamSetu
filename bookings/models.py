from django.db import models
from django.contrib.auth.models import User
from workers.models import Worker
from django.core.validators import MinValueValidator, MaxValueValidator


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

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="customer_bookings",
        null=True,
        blank=True
    )

    customer_name = models.CharField(
        max_length=100
    )

    customer_mobile = models.CharField(
        max_length=15,
        blank=True
    )

    customer_address = models.TextField()

    work_date = models.DateField()

    work_description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.customer_name} - {self.worker.name}"

from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="review"
    )

    worker = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name="worker_reviews"
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    title = models.CharField(
        max_length=100,
        blank=True
    )

    comment = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.worker.name} ({self.rating}⭐)"