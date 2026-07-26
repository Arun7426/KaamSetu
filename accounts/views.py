from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .forms import CustomerRegistrationForm


def register(request):

    if request.method == "POST":

        form = CustomerRegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect("home")

    else:

        form = CustomerRegistrationForm()

    return render(
        request,
        "register.html",
        {
            "form": form
        }
    )

def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

                # Admin
            if user.is_staff:
                return redirect("/admin/")

                # Worker
            elif hasattr(user, "worker_profile"):
                return redirect("worker_dashboard")

                # Customer
            else:
                return redirect("customer_dashboard")

        else:
            messages.error(request, "Invalid Username or Password")

    else:

            messages.error(request, "Invalid Username or Password")

    return render(request, "login.html")


def user_logout(request):

    logout(request)

    return redirect("home")

from django.contrib.auth.decorators import login_required
from bookings.models import Booking


@login_required
def customer_dashboard(request):

    bookings = Booking.objects.filter(
        customer=request.user
    ).order_by("-created_at")

    return render(
        request,
        "customer_dashboard.html",
        {
            "bookings": bookings
        }
    )