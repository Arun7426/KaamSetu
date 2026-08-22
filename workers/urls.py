from django.urls import path
from . import views


urlpatterns = [

    # =========================================
    # Home
    # =========================================

    path(
        "",
        views.home,
        name="home",
    ),

    # =========================================
    # Worker
    # =========================================

    path(
        "workers/<int:worker_id>/",
        views.worker_detail,
        name="worker_detail",
    ),

    path(
        "worker/register/",
        views.worker_register,
        name="worker_register",
    ),

    path(
        "worker/dashboard/",
        views.worker_dashboard,
        name="worker_dashboard",
    ),
    
    path(
        "worker/edit-profile/",
        views.edit_worker_profile,
        name="edit_worker_profile",
    ),

    path(
        "worker/toggle-availability/",
        views.toggle_availability,
        name="toggle_availability",
    ),

    path(
        "worker/update-location/",
        views.update_worker_location,
        name="update_worker_location",
    ),

    path(
        "worker/update-work-range/",
        views.update_work_range,
        name="update_work_range",
    ),

    # =========================================
    # Booking Status
    # =========================================

    path(
        "booking/<int:booking_id>/<str:status>/",
        views.update_booking_status,
        name="update_booking_status",
    ),

    # =========================================
    # Profession
    # =========================================

    path(
        "profession/<str:profession>/",
        views.workers_by_profession,
        name="workers_by_profession",
    ),

    # =========================================
    # Company Pages
    # =========================================

    path(
        "about/",
        views.about,
        name="about",
    ),

    path(
        "privacy-policy/",
        views.privacy_policy,
        name="privacy_policy",
    ),

    path(
        "terms-conditions/",
        views.terms_conditions,
        name="terms_conditions",
    ),

]