from django.db import models


class Vacancy(models.Model):
    """
    Careers / Volunteer Internship vacancy.
    Vacancies are managed from the Admin Panel.
    """

    title = models.CharField(max_length=200)

    short_description = models.CharField(
        max_length=300
    )

    description = models.TextField()

    eligibility = models.TextField(
        blank=True
    )

    location = models.CharField(
        max_length=150,
        blank=True
    )

    internship_type = models.CharField(
        max_length=100,
        default="Volunteer Internship"
    )

    stipend = models.CharField(
        max_length=100,
        blank=True
    )

    openings = models.PositiveIntegerField(
        default=1
    )

    application_deadline = models.DateField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
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
        return self.title


class Application(models.Model):
    """
    Online application submitted against a specific vacancy.
    """

    STATUS_CHOICES = [
        ("APPLIED", "Applied"),
        ("UNDER_REVIEW", "Under Review"),
        ("SHORTLISTED", "Shortlisted"),
        ("INTERVIEW", "Interview"),
        ("SELECTED", "Selected"),
        ("REJECTED", "Rejected"),
    ]

    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    full_name = models.CharField(
        max_length=150
    )

    email = models.EmailField()

    mobile = models.CharField(
        max_length=15
    )

    education = models.CharField(
        max_length=200,
        blank=True
    )

    experience = models.CharField(
        max_length=200,
        blank=True
    )

    cover_letter = models.TextField(
        blank=True
    )

    cv = models.FileField(
        upload_to="careers/cv/"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="APPLIED"
    )

    admin_notes = models.TextField(
        blank=True
    )

    interview_date = models.DateTimeField(
        null=True,
        blank=True
    )

    interview_notes = models.TextField(
        blank=True
    )

    certificate_eligible = models.BooleanField(
        default=False
    )

    certificate_issued = models.BooleanField(
        default=False
    )

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.full_name} - {self.vacancy.title}"
    