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
    
    path(
        "api/v1/",
        include("api.urls")
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

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT,
)