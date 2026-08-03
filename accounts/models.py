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

    def __str__(self):
        return self.user.username