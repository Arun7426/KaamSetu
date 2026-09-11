from django.contrib import admin

from .models import Application, Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "internship_type",
        "location",
        "openings",
        "application_deadline",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "internship_type",
        "created_at",
    )

    search_fields = (
        "title",
        "short_description",
        "description",
    )

    ordering = ("-created_at",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "vacancy",
        "email",
        "mobile",
        "status",
        "certificate_eligible",
        "certificate_issued",
        "applied_at",
    )

    list_filter = (
        "status",
        "certificate_eligible",
        "certificate_issued",
        "applied_at",
    )

    search_fields = (
        "full_name",
        "email",
        "mobile",
        "vacancy__title",
    )

    readonly_fields = (
        "applied_at",
        "updated_at",
    )

    ordering = ("-applied_at",)