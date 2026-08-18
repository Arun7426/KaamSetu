from django.db import models
from django.contrib.auth.models import User


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile"
    )

    mobile = models.CharField(
        max_length=10,
        unique=True
    )
    mobile_verified = models.BooleanField(
        default=False
    )
    address = models.TextField(
        blank=True,
        null=True
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.user.username
