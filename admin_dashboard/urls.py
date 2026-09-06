from django.urls import path

from . import views
from . import admin_management


urlpatterns = [

    # =====================================================
    # ADMIN DASHBOARD
    # =====================================================

    path(
        "",
        views.admin_dashboard,
        name="admin_dashboard"
    ),


    # =====================================================
    # MANAGEMENT
    # =====================================================

    path(
        "workers/",
        views.admin_workers,
        name="admin_workers"
    ),

    path(
        "customers/",
        views.admin_customers,
        name="admin_customers"
    ),

    path(
        "bookings/",
        views.admin_bookings,
        name="admin_bookings"
    ),

    path(
        "reviews/",
        views.admin_reviews,
        name="admin_reviews"
    ),
    
    path(
        "notifications/",
        views.admin_notifications,
        name="admin_notifications"
    ),
    
        # =====================================================
    # ANALYTICS
    # =====================================================

    path(
        "insights/",
        views.admin_insights,
        name="admin_insights"
    ),
    
    # =====================================================
    # FINANCE
    # =====================================================

    path(
        "payments/",
        views.admin_payments,
        name="admin_payments"
    ),
    
    path(
        "payment-alerts/",
        views.admin_payment_alerts,
        name="admin_payment_alerts"
    ),
    
    path(
        "payment-alerts/<int:alert_id>/",
        views.admin_payment_alert_detail,
        name="admin_payment_alert_detail"
    ),
    
    path(
        "payment-alerts/<int:alert_id>/follow-up/",
        views.admin_payment_alert_follow_up,
        name="admin_payment_alert_follow_up"
    ),

    path(
        "payment-alerts/<int:alert_id>/send-sms/",
        views.admin_payment_alert_send_sms,
        name="admin_payment_alert_send_sms"
    ),
    
    path(
        "worker-ledger/",
        views.admin_worker_ledger,
        name="admin_worker_ledger"
    ),

    path(
        "fee-settings/",
        views.admin_fee_settings,
        name="admin_fee_settings"
    ),

    path(
        "promotions/",
        views.admin_promotions,
        name="admin_promotions"
    ),

    path(
        "promotions/create/",
        views.admin_promotion_create,
        name="admin_promotion_create"
    ),

    path(
        "promotions/<int:promotion_id>/edit/",
        views.admin_promotion_edit,
        name="admin_promotion_edit"
    ),

    path(
        "promotions/<int:promotion_id>/toggle/",
        views.admin_promotion_toggle,
        name="admin_promotion_toggle"
    ),

    path(
        "promotions/<int:promotion_id>/delete/",
        views.admin_promotion_delete,
        name="admin_promotion_delete"
    ),

    # =====================================================
    # ADMIN MANAGEMENT
    # =====================================================

    path(
        "admin-management/",
        views.admin_management,
        name="admin_management"
    ),

    path(
        "admin-management/create/",
        admin_management.create_admin,
        name="create_admin"
    ),

    path(
        "admin-management/edit/<int:user_id>/",
        admin_management.edit_admin,
        name="edit_admin"
    ),

]