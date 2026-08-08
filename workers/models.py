from django.db import models
from django.contrib.auth.models import User


class Worker(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="worker_profile"
    )
    PROFESSION_CHOICES = [
    ("Rajmistri", "राजमिस्त्री"),
    ("Plumber", "प्लम्बर"),
    ("Electrician", "इलेक्ट्रिशियन"),
    ("Painter", "पेंटर"),
    ("Carpenter", "कारपेंटर"),
    ("Welder", "वेल्डर"),
    ("Helper", "हेल्पर"),
    ("AC Repair", "AC रिपेयर"),
]

    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    profession = models.CharField(max_length=30, choices=PROFESSION_CHOICES)
    experience = models.PositiveIntegerField(help_text="Experience in years")
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    work_range = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text="Maximum distance in KM"
    )
    daily_wage = models.DecimalField(max_digits=8, decimal_places=2)
    about = models.TextField(blank=True)
    available = models.BooleanField(default=True)
    profile_photo = models.ImageField(upload_to="workers/", blank=True, null=True)


    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    reviews = models.PositiveIntegerField(default=0)
    vverified = models.BooleanField(default=False)

    def __str__(self):
        return self.name
