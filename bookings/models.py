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

    NEGOTIATION_STATUS_CHOICES = [
        ("Not Started", "Not Started"),
        ("Customer Offered", "Customer Offered"),
        ("Worker Countered", "Worker Countered"),
        ("Accepted", "Accepted"),
        ("Rejected", "Rejected"),
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

    # ---------------------------------
    # Negotiation Fields
    # ---------------------------------

    original_amount = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(9999)
        ],
        null=True,
        blank=True
    )

    customer_offer = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(9999)
        ],
        null=True,
        blank=True
    )

    worker_counter_offer = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(9999)
        ],
        null=True,
        blank=True
    )

    final_amount = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(9999)
        ],
        null=True,
        blank=True
    )

    negotiation_status = models.CharField(
        max_length=20,
        choices=NEGOTIATION_STATUS_CHOICES,
        default="Not Started"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.customer_name} - {self.worker.name}"


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


# =========================================
# Notification
# =========================================

class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ("booking", "Booking"),
        ("offer", "Offer"),
        ("counter_offer", "Counter Offer"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )

    message = models.CharField(
        max_length=255
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.recipient.username} - {self.message}"