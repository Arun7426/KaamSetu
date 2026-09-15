from django.db import models
from django.utils import timezone


class MobileOTP(models.Model):
    PURPOSE_CHOICES = [
        ("registration", "Registration"),
        ("login", "Login"),
        ("website_login_setup", "Website Login Setup"),
    ]
    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("worker", "Worker"),
    ]

    mobile = models.CharField(max_length=10, db_index=True)
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="customer",
    )

    otp_hash = models.CharField(max_length=64)

    purpose = models.CharField(
        max_length=30,
        choices=PURPOSE_CHOICES,
        default="registration",
    )

    attempts = models.PositiveIntegerField(default=0)

    is_verified = models.BooleanField(default=False)

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    consumed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"{self.mobile} - {self.purpose}"