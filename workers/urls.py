from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("worker/<int:worker_id>/", views.worker_detail, name="worker_detail"),
]

