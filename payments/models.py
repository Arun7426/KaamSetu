from django.db import models
from workers.models import Worker
from bookings.models import Booking


class FeeSetting(models.Model):

    FEE_TYPE_CHOICES = [
        ("fixed", "Fixed Amount"),
        ("percentage", "Percentage"),
    ]

    fee_type = models.CharField(
        max_length=20,
        choices=FEE_TYPE_CHOICES,
        default="fixed"
    )

    fee_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=20.00
    )

    is_active = models.BooleanField(
        default=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        if self.fee_type == "fixed":
            return f"Platform Fee: ₹{self.fee_value}"
        return f"Platform Fee: {self.fee_value}%"

    class Meta:
        verbose_name = "Fee Setting"
        verbose_name_plural = "Fee Setting"


class Promotion(models.Model):

    name = models.CharField(
        max_length=100
    )

    is_active = models.BooleanField(
        default=True
    )

    free_bookings_limit = models.PositiveIntegerField(
        default=10,
        help_text="Number of final accepted bookings for which platform fee is waived."
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class WorkerLedger(models.Model):

    TRANSACTION_TYPES = [
        ("Booking Fee", "Booking Fee"),
        ("Payment", "Payment"),
    ]

    PAYMENT_STATUS = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
    ]

    worker = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name="ledger_entries"
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries"
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES
    )

    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="Pending"
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"{self.worker.name} - "
            f"₹{self.amount} - "
            f"{self.transaction_type}"
        )