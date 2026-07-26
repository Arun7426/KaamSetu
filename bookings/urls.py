from django.urls import path
from . import views

urlpatterns = [
    path(
        "worker/<int:worker_id>/book/",
        views.book_worker,
        name="book_worker",
    ),
]