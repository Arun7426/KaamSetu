from django.db import models


class Worker(models.Model):
    PROFESSION_CHOICES = [
        ("Plumber", "Plumber"),
        ("Electrician", "Electrician"),
        ("Carpenter", "Carpenter"),
        ("Painter", "Painter"),
        ("Mason", "Mason"),
        ("Welder", "Welder"),
        ("Cleaner", "Cleaner"),
        ("Driver", "Driver"),
        ("Other", "Other"),
    ]

    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    profession = models.CharField(max_length=30, choices=PROFESSION_CHOICES)
    experience = models.PositiveIntegerField(help_text="Experience in years")
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    daily_wage = models.DecimalField(max_digits=8, decimal_places=2)
    about = models.TextField(blank=True)
    available = models.BooleanField(default=True)
    profile_photo = models.ImageField(upload_to="workers/", blank=True, null=True)

    def __str__(self):
        return self.name