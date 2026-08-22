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


    # =====================================================
    # FINANCE
    # =====================================================

    path(
        "payments/",
        views.admin_payments,
        name="admin_payments"
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