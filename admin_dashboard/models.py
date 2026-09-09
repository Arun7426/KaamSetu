from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("OTHER", "Other"),
    ]

    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )

    module = models.CharField(
        max_length=100,
    )

    description = models.TextField()

    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="targeted_audit_logs",
    )

    target_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        admin_name = self.admin.username if self.admin else "System"
        return f"{admin_name} - {self.action} - {self.module}"
    
class SystemSetting(models.Model):
    maintenance_mode = models.BooleanField(
        default=False,
    )

    maintenance_message = models.TextField(
        blank=True,
        default="KaamSetu is currently under maintenance. Please check back soon.",
    )

    support_email = models.EmailField(
        blank=True,
    )

    support_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    app_version = models.CharField(
        max_length=50,
        default="1.0.0",
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_settings_updates",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return "KaamSetu System Settings"