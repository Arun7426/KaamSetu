from django.contrib import admin
from django.urls import path, include
from django.conf import settings



urlpatterns = [

    path("admin/", admin.site.urls),
    path(
        "admin-control/",
        include("admin_dashboard.urls")
    ),


    # Booking & Negotiation URLs first
    path("", include("bookings.urls")),

    # Worker URLs
    path("", include("workers.urls")),

    # Account URLs
    path("", include("accounts.urls")),

    path(
        "payments/",
        include("payments.urls")
    ),
    
    path(
        "careers/",
        include("careers.urls")
    ),

]

if settings.SERVE_MEDIA_LOCALLY:
    from django.views.static import serve

    urlpatterns += [
        path(
            "media/<path:path>",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]