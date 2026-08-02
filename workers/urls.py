from django.urls import path
from . import views

urlpatterns = [

    path("", views.home, name="home"),

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
        "booking/<int:booking_id>/<str:status>/",
        views.update_booking_status,
        name="update_booking_status",
    ),
    path(
        "profession/<str:profession>/",
        views.workers_by_profession,
        name="workers_by_profession",
    ),

]