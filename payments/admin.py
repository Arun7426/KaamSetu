from django.contrib import admin

from .models import FeeSetting, Promotion, WorkerLedger


@admin.register(FeeSetting)
class FeeSettingAdmin(admin.ModelAdmin):
    list_display = (
        "fee_type",
        "fee_value",
        "is_active",
        "updated_at",
    )


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "free_bookings_limit",
        "created_at",
        "updated_at",
    )


@admin.register(WorkerLedger)
class WorkerLedgerAdmin(admin.ModelAdmin):
    list_display = (
        "worker",
        "booking",
        "transaction_type",
        "amount",
        "status",
        "created_at",
        "paid_at",
    )

    list_filter = (
        "transaction_type",
        "status",
    )

    search_fields = (
        "worker__name",
        "worker__mobile",
    )