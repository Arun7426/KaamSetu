from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


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

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )