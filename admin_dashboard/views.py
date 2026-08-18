from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Sum, Q

from workers.models import Worker
from bookings.models import Booking
from payments.models import WorkerLedger


def staff_required(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(staff_required, login_url="login")
def admin_dashboard(request):

    # -----------------------------------------
    # USER COUNTS
    # -----------------------------------------

    total_users = User.objects.count()

    total_workers = Worker.objects.count()

    total_customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True
    ).count()


    # -----------------------------------------
    # BOOKING COUNTS
    # -----------------------------------------

    total_bookings = Booking.objects.count()

    pending_bookings = Booking.objects.filter(
        status="Pending"
    ).count()

    accepted_bookings = Booking.objects.filter(
        status="Accepted"
    ).count()

    completed_bookings = Booking.objects.filter(
        status="Completed"
    ).count()

    cancelled_bookings = Booking.objects.filter(
        status="Cancelled"
    ).count()


    # -----------------------------------------
    # PAYMENT / LEDGER
    # -----------------------------------------

    total_outstanding = sum(
        entry.amount
        for entry in WorkerLedger.objects.filter(
            transaction_type="Booking Fee",
            status="Pending"
        )
    )

    total_paid = sum(
        entry.amount
        for entry in WorkerLedger.objects.filter(
            transaction_type="Booking Fee",
            status="Paid"
        )
    )

        # -----------------------------------------
    # WORKER-WISE OUTSTANDING
    # -----------------------------------------

    workers_with_outstanding = Worker.objects.annotate(
        outstanding=Sum(
            "ledger_entries__amount",
            filter=Q(
                ledger_entries__transaction_type="Booking Fee",
                ledger_entries__status="Pending"
            )
        )
    ).filter(
        outstanding__gt=0
    ).order_by(
        "-outstanding"
    )


    # -----------------------------------------
    # RECENT BOOKINGS
    # -----------------------------------------

    recent_bookings = Booking.objects.select_related(
        "worker",
        "customer"
    ).order_by(
        "-created_at"
    )[:10]

 # -----------------------------------------
    # RECENT ACTIVITY
    # -----------------------------------------

    recent_customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True
    ).order_by(
        "-date_joined"
    )[:5]


    recent_workers = Worker.objects.select_related(
        "user"
    ).order_by(
        "-user__date_joined"
    )[:5]


    recent_payments = WorkerLedger.objects.select_related(
        "worker",
        "booking"
    ).order_by(
        "-created_at"
    )[:5]


    return render(
        request,
        "admin_dashboard/dashboard.html",
        {
            "total_users": total_users,
            "total_workers": total_workers,
            "total_customers": total_customers,

            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "accepted_bookings": accepted_bookings,
            "completed_bookings": completed_bookings,
            "cancelled_bookings": cancelled_bookings,

            "total_outstanding": total_outstanding,
            "total_paid": total_paid,

            "workers_with_outstanding": workers_with_outstanding,

            "recent_bookings": recent_bookings,
            "recent_customers": recent_customers,
            "recent_workers": recent_workers,
            "recent_payments": recent_payments,
        }
    )
   


@user_passes_test(staff_required, login_url="login")
def admin_workers(request):

    workers = Worker.objects.select_related(
        "user"
    ).order_by(
        "name"
    )

    return render(
        request,
        "admin_dashboard/workers.html",
        {
            "workers": workers,
        }
    )

@user_passes_test(staff_required, login_url="login")
def admin_customers(request):

    customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True
    ).order_by(
        "username"
    )

    return render(
        request,
        "admin_dashboard/customers.html",
        {
            "customers": customers,
        }
    )

@user_passes_test(staff_required, login_url="login")
def admin_bookings(request):

    bookings = Booking.objects.select_related(
        "worker",
        "customer"
    ).order_by(
        "-created_at"
    )

    status_filter = request.GET.get("status")

    if status_filter in [
        "Pending",
        "Accepted",
        "Completed",
        "Cancelled",
    ]:
        bookings = bookings.filter(
            status=status_filter
        )

    return render(
        request,
        "admin_dashboard/bookings.html",
        {
            "bookings": bookings,
            "status_filter": status_filter,
        }
    )

@user_passes_test(staff_required, login_url="login")
def admin_payments(request):

    ledger_entries = WorkerLedger.objects.select_related(
        "worker",
        "booking"
    ).order_by(
        "-created_at"
    )

    status_filter = request.GET.get("status")
    transaction_filter = request.GET.get("transaction")

    if status_filter in ["Pending", "Paid"]:
        ledger_entries = ledger_entries.filter(
            status=status_filter
        )

    if transaction_filter in ["Booking Fee", "Payment"]:
        ledger_entries = ledger_entries.filter(
            transaction_type=transaction_filter
        )

    return render(
        request,
        "admin_dashboard/payments.html",
        {
            "ledger_entries": ledger_entries,
            "status_filter": status_filter,
            "transaction_filter": transaction_filter,
        }
    )