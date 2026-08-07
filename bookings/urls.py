from django.urls import path
from . import views


urlpatterns = [
    path(
        "worker/<int:worker_id>/book/",
        views.book_worker,
        name="book_worker",
    ),

    path(
        "booking/success/<int:booking_id>/",
        views.booking_success,
        name="booking_success",
    ),
    path(
        "review/<int:booking_id>/",
        views.add_review,
        name="add_review",
    ),
]