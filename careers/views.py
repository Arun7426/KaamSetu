from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ApplicationForm
from .models import Vacancy


def vacancy_list(request):
    """
    Public Careers page.
    Shows currently active vacancies.
    """

    vacancies = Vacancy.objects.filter(
        is_active=True
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "careers/vacancy_list.html",
        {
            "vacancies": vacancies,
        }
    )


def vacancy_detail(request, vacancy_id):
    """
    Public vacancy details and online application form.
    """

    vacancy = get_object_or_404(
        Vacancy,
        id=vacancy_id,
        is_active=True,
    )

    form = ApplicationForm()

    if request.method == "POST":
        form = ApplicationForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            application = form.save(
                commit=False
            )

            application.vacancy = vacancy
            application.save()

            messages.success(
                request,
                "Your application has been submitted successfully."
            )

            return redirect(
                "careers_vacancy_detail",
                vacancy_id=vacancy.id,
            )

    return render(
        request,
        "careers/vacancy_detail.html",
        {
            "vacancy": vacancy,
            "form": form,
        }
    )