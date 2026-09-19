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

class WorkerPaymentTransaction(models.Model):

    STATUS_CHOICES = [
        ("Created", "Created"),
        ("Pending", "Pending"),
        ("Verified", "Verified"),
        ("Failed", "Failed"),
        ("Cancelled", "Cancelled"),
    ]

    worker = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name="payment_transactions"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Created"
    )

    provider = models.CharField(
        max_length=50,
        blank=True
    )

    provider_order_id = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    provider_payment_id = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.worker.name} - "
            f"₹{self.amount} - "
            f"{self.status}"
        )

        
class WorkerPaymentAlert(models.Model):

    ALERT_TYPE_CHOICES = [
        ("Outstanding Limit", "Outstanding Limit"),
    ]

    ALERT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Follow-up", "Follow-up"),
        ("Resolved", "Resolved"),
    ]

    SMS_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Sent", "Sent"),
        ("Failed", "Failed"),
    ]

    worker = models.ForeignKey(
        "workers.Worker",
        on_delete=models.CASCADE,
        related_name="payment_alerts"
    )

    alert_type = models.CharField(
        max_length=50,
        choices=ALERT_TYPE_CHOICES,
        default="Outstanding Limit"
    )

    outstanding_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    threshold_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=200
    )

    status = models.CharField(
        max_length=20,
        choices=ALERT_STATUS_CHOICES,
        default="Pending"
    )

    sms_status = models.CharField(
        max_length=20,
        choices=SMS_STATUS_CHOICES,
        default="Pending"
    )

    sms_sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    sms_error = models.TextField(
        blank=True,
        null=True
    )

    last_follow_up_at = models.DateTimeField(
        null=True,
        blank=True
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.worker.name} - "
            f"₹{self.outstanding_amount} - "
            f"{self.status}"
        )