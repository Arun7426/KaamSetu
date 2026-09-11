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

    # =====================================================
    # FRAUD CONTROL - SUPER ADMIN ONLY
    # =====================================================

    path(
        "fraud-control/",
        views.admin_fraud_control,
        name="admin_fraud_control"
    ),

    path(
        "fraud-control/worker/<int:worker_id>/toggle-block/",
        views.admin_toggle_worker_block,
        name="admin_toggle_worker_block"
    ),

    path(
        "fraud-control/customer/<int:user_id>/toggle-block/",
        views.admin_toggle_customer_block,
        name="admin_toggle_customer_block"
    ),

    path(
        "fraud-control/worker/<int:worker_id>/delete/",
        views.admin_delete_worker,
        name="admin_delete_worker"
    ),

    path(
        "fraud-control/customer/<int:user_id>/delete/",
        views.admin_delete_customer,
        name="admin_delete_customer"
    ),

    path(
        "bookings/",
        views.admin_bookings,
        name="admin_bookings"
    ),
    
    path(
        "bookings/expire-pending/",
        views.expire_pending_bookings_manual,
        name="expire_pending_bookings_manual"
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
    
    path(
        "reports/",
        views.admin_reports,
        name="admin_reports"
    ),
    
    
    path(
        "reports/export/excel/",
        views.export_report_excel,
        name="export_report_excel",
    ),

    path(
        "reports/export/pdf/",
        views.export_report_pdf,
        name="export_report_pdf",
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

    path(
        "admin-management/change-password/<int:user_id>/",
        admin_management.change_admin_password,
        name="change_admin_password"
    ),

    path(
        "admin-management/delete/<int:user_id>/",
        admin_management.delete_admin,
        name="delete_admin"
    ),

    # =====================================================
    # AUDIT LOGS
    # =====================================================

    path(
        "audit-logs/",
        views.admin_audit_logs,
        name="admin_audit_logs"
    ),
    
    path(
        "system-settings/",
        views.admin_system_settings,
        name="admin_system_settings"
    ),

    path(
        "password-management/super-admin/",
        views.change_super_admin_password,
        name="change_super_admin_password"
    ),
]