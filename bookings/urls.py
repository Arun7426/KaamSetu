from django.urls import path
from . import views


urlpatterns = [

    # =========================================
    # Booking
    # =========================================

    path(
        "book/<int:worker_id>/",
        views.book_worker,
        name="book_worker",
    ),

    path(
        "success/<int:booking_id>/",
        views.booking_success,
        name="booking_success",
    ),

    # =========================================
    # Customer - Negotiation
    # =========================================

    path(
        "booking/<int:booking_id>/make-offer/",
        views.customer_make_offer,
        name="customer_make_offer",
    ),

    path(
        "booking/<int:booking_id>/counter-response/",
        views.customer_respond_counter,
        name="customer_respond_counter",
    ),

    # =========================================
    # Worker - Negotiation
    # =========================================

    path(
        "booking/<int:booking_id>/respond-offer/",
        views.worker_respond_offer,
        name="worker_respond_offer",
    ),

    # =========================================
    # Notifications
    # =========================================

    path(
        "notifications/",
        views.notifications,
        name="notifications",
    ),

    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),

    path(
        "notifications/read-all/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),

    # =========================================
    # Review
    # =========================================

    path(
        "review/<int:booking_id>/",
        views.add_review,
        name="add_review",
    ),
]