from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

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

]