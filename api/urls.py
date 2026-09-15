from django.urls import path

from .views import (
    api_status,
    send_otp,
    verify_otp,
    register_mobile_user,
    current_user,
    setup_website_login,
    worker_list,
    worker_detail,
    my_profile,
    create_booking,
    booking_list,
    booking_detail,
    customer_make_offer_api,
    worker_respond_offer_api,
    customer_respond_counter_api,
    worker_update_booking_status_api,
    add_review_api,
)


urlpatterns = [
    # -------------------------------------------------
    # API STATUS
    # -------------------------------------------------

    path(
        "status/",
        api_status,
        name="api-status",
    ),

    # -------------------------------------------------
    # AUTH
    # -------------------------------------------------

    path(
        "auth/send-otp/",
        send_otp,
        name="send-otp",
    ),

    path(
        "auth/verify-otp/",
        verify_otp,
        name="verify-otp",
    ),

    path(
        "auth/register/",
        register_mobile_user,
        name="mobile-register",
    ),

    path(
        "auth/me/",
        current_user,
        name="current-user",
    ),

    path(
        "auth/website-login/setup/",
        setup_website_login,
        name="website-login-setup",
    ),

    # -------------------------------------------------
    # MODULE 2 — WORKER DISCOVERY
    # -------------------------------------------------

    path(
        "workers/",
        worker_list,
        name="worker-list",
    ),

    path(
        "workers/<int:worker_id>/",
        worker_detail,
        name="worker-detail",
    ),

    # -------------------------------------------------
    # MODULE 3 — PROFILE
    # -------------------------------------------------

    path(
        "profile/",
        my_profile,
        name="my-profile",
    ),

    # -------------------------------------------------
    # MODULE 4 — BOOKING
    # -------------------------------------------------

    path(
        "bookings/",
        booking_list,
        name="booking-list",
    ),

    path(
        "bookings/create/",
        create_booking,
        name="booking-create",
    ),

    path(
        "bookings/<int:booking_id>/",
        booking_detail,
        name="booking-detail",
    ),

    path(
        "bookings/<int:booking_id>/status/",
        worker_update_booking_status_api,
        name="worker-update-booking-status",
    ),
    
    # -------------------------------------------------
    # MODULE 4 — BOOKING NEGOTIATION
    # -------------------------------------------------

    path(
        "bookings/<int:booking_id>/offer/",
        customer_make_offer_api,
        name="customer-make-offer",
    ),

    path(
        "bookings/<int:booking_id>/offer/respond/",
        worker_respond_offer_api,
        name="worker-respond-offer",
    ),

    path(
        "bookings/<int:booking_id>/counter/respond/",
        customer_respond_counter_api,
        name="customer-respond-counter",
    ),
    
    # -------------------------------------------------
    # MODULE 5 — REVIEWS & RATINGS
    # -------------------------------------------------

    path(
        "bookings/<int:booking_id>/review/",
        add_review_api,
        name="booking-review",
    ),
]