from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.vacancy_list,
        name="careers_vacancy_list",
    ),

    path(
        "<int:vacancy_id>/",
        views.vacancy_detail,
        name="careers_vacancy_detail",
    ),
]