from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.db.models import Sum, Q, Avg, Count
from django.core.exceptions import PermissionDenied

from functools import wraps

from workers.models import Worker
from bookings.models import Booking, Review, Notification
from payments.models import WorkerLedger, WorkerPaymentAlert



# =========================================================
# EXISTING STAFF CHECK
# =========================================================

def staff_required(user):
    return user.is_authenticated and user.is_staff


# =========================================================
# KAAMSETU ADMIN ROLE
# =========================================================

def get_admin_role(user):
    """
    Two-level KaamSetu Admin architecture.

    SUPER_ADMIN:
        Django superuser

    ADMIN:
        Django staff user who is not a superuser

    NONE:
        Any other user
    """

    if not user or not user.is_authenticated:
        return "NONE"

    if user.is_superuser:
        return "SUPER_ADMIN"

    if user.is_staff:
        return "ADMIN"

    return "NONE"


# =========================================================
# KAAMSETU ADMIN ROLE FOUNDATION
# =========================================================

def admin_required(view_func):
    """
    Allow only KaamSetu Admin or Super Admin users.

    Super Admin:
        is_superuser = True

    Admin:
        is_staff = True
        is_superuser = False
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        # -------------------------------------------------
        # SUPER ADMIN
        # -------------------------------------------------

        if request.user.is_superuser:
            return view_func(
                request,
                *args,
                **kwargs
            )

        # -------------------------------------------------
        # NORMAL ADMIN
        # -------------------------------------------------

        if request.user.is_staff:
            return view_func(
                request,
                *args,
                **kwargs
            )

        # -------------------------------------------------
        # CUSTOMER / WORKER / NORMAL USER
        # -------------------------------------------------

        raise PermissionDenied(
            "You do not have permission to access the KaamSetu Admin Panel."
        )

    return wrapper


# =========================================================
# KAAMSETU PERMISSION REQUIRED
# =========================================================

def permission_required(permission_name):
    """
    Allow Super Admin automatically.

    Normal Admin users must have the
    specified Django permission.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("login")

            # -------------------------------------------------
            # SUPER ADMIN
            # -------------------------------------------------

            if request.user.is_superuser:
                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            # -------------------------------------------------
            # NORMAL ADMIN
            # -------------------------------------------------

            if (
                request.user.is_staff
                and request.user.has_perm(permission_name)
            ):
                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            raise PermissionDenied(
                "You do not have permission to access this section."
            )

        return wrapper

    return decorator

# =========================================================
# SUPER ADMIN ONLY
# =========================================================

def super_admin_required(view_func):
    """
    Allow ONLY Django Super Admin users.

    Normal Admin users are explicitly denied.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_superuser:
            raise PermissionDenied(
                "Only Super Admin can access this section."
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper

# =========================================================
# ADMIN DASHBOARD
# =========================================================

@admin_required
def admin_dashboard(request):

    role = get_admin_role(request.user)

    # =====================================================
    # USER COUNTS
    # =====================================================

    total_users = User.objects.count()

    total_workers = Worker.objects.count()

    total_customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True
    ).count()

    # =====================================================
    # BOOKING COUNTS
    # =====================================================

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

    # =====================================================
    # FINANCE
    # SUPER ADMIN ONLY
    # =====================================================

    total_outstanding = None
    total_paid = None

    workers_with_outstanding = Worker.objects.none()
    recent_payments = WorkerLedger.objects.none()

    if request.user.is_superuser:

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

        recent_payments = WorkerLedger.objects.select_related(
            "worker",
            "booking"
        ).order_by(
            "-created_at"
        )[:5]

    # =====================================================
    # RECENT BOOKINGS
    # =====================================================

    recent_bookings = Booking.objects.select_related(
        "worker",
        "customer"
    ).order_by(
        "-created_at"
    )[:10]

    # =====================================================
    # RECENT CUSTOMERS
    # =====================================================

    recent_customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True
    ).order_by(
        "-date_joined"
    )[:5]

    # =====================================================
    # RECENT WORKERS
    # =====================================================

    recent_workers = Worker.objects.select_related(
        "user"
    ).order_by(
        "-user__date_joined"
    )[:5]

    return render(
        request,
        "admin_dashboard/dashboard.html",
        {
            "admin_role": role,

            # -------------------------------------------------
            # USER STATISTICS
            # -------------------------------------------------

            "total_users": total_users,
            "total_workers": total_workers,
            "total_customers": total_customers,

            # -------------------------------------------------
            # BOOKING STATISTICS
            # -------------------------------------------------

            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "accepted_bookings": accepted_bookings,
            "completed_bookings": completed_bookings,
            "cancelled_bookings": cancelled_bookings,

            # -------------------------------------------------
            # FINANCE
            # SUPER ADMIN ONLY
            # -------------------------------------------------

            "total_outstanding": total_outstanding,
            "total_paid": total_paid,
            "workers_with_outstanding":
                workers_with_outstanding,
            "recent_payments":
                recent_payments,

            # -------------------------------------------------
            # RECENT ACTIVITY
            # -------------------------------------------------

            "recent_bookings":
                recent_bookings,
            "recent_customers":
                recent_customers,
            "recent_workers":
                recent_workers,
        }
    )


# =========================================================
# WORKERS
# =========================================================

@permission_required("workers.view_worker")
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


# =========================================================
# CUSTOMERS
# =========================================================

@permission_required("auth.view_user")
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


# =========================================================
# BOOKINGS
# =========================================================

@permission_required("bookings.view_booking")
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

# =========================================================
# REVIEWS
# =========================================================

@permission_required("bookings.view_review")
def admin_reviews(request):

    # =====================================================
    # ALL REVIEWS
    # =====================================================

    reviews = Review.objects.select_related(
        "booking",
        "worker",
        "customer"
    ).order_by(
        "-created_at"
    )

    # =====================================================
    # RATING FILTER
    # =====================================================

    rating_filter = request.GET.get("rating")

    if rating_filter in [
        "1",
        "2",
        "3",
        "4",
        "5",
    ]:
        reviews = reviews.filter(
            rating=int(rating_filter)
        )

    # =====================================================
    # REVIEW STATISTICS
    # =====================================================

    review_stats = Review.objects.aggregate(
        total=Count("id"),
        average=Avg("rating"),
    )

    total_reviews = review_stats["total"] or 0
    average_rating = review_stats["average"] or 0

    five_star_reviews = Review.objects.filter(
        rating=5
    ).count()

    low_rating_reviews = Review.objects.filter(
        rating__lte=2
    ).count()

    # =====================================================
    # CONTEXT
    # =====================================================

    return render(
        request,
        "admin_dashboard/reviews.html",
        {
            "reviews": reviews,

            "total_reviews":
                total_reviews,

            "average_rating":
                round(average_rating, 1),

            "five_star_reviews":
                five_star_reviews,

            "low_rating_reviews":
                low_rating_reviews,

            "rating_filter":
                rating_filter,
        }
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

@permission_required("bookings.view_notification")
def admin_notifications(request):

    notifications = Notification.objects.select_related(
        "recipient",
        "booking",
    ).order_by(
        "-created_at"
    )

    total_notifications = Notification.objects.count()

    unread_notifications = Notification.objects.filter(
        is_read=False
    ).count()

    read_notifications = Notification.objects.filter(
        is_read=True
    ).count()

    return render(
        request,
        "admin_dashboard/notifications.html",
        {
            "notifications": notifications,
            "total_notifications": total_notifications,
            "unread_notifications": unread_notifications,
            "read_notifications": read_notifications,
        }
    )

# =========================================================
# PAYMENTS
# =========================================================

@permission_required("payments.view_workerledger")
def admin_payments(request):

    ledger_entries = WorkerLedger.objects.select_related(
        "worker",
        "booking"
    ).order_by(
        "-created_at"
    )

    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    status_filter = request.GET.get("status")

    if status_filter in [
        "Pending",
        "Paid",
    ]:
        ledger_entries = ledger_entries.filter(
            status=status_filter
        )

    # -----------------------------------------------------
    # TRANSACTION FILTER
    # -----------------------------------------------------

    transaction_filter = request.GET.get("transaction")

    if transaction_filter in [
        "Booking Fee",
        "Payment",
    ]:
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

# =========================================================
# PAYMENT ALERTS
# SUPER ADMIN ONLY
# =========================================================

def super_admin_only(view_func):
    """
    Allow ONLY Django Super Admin users.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_superuser:
            raise PermissionDenied(
                "Only Super Admin can access Payment Alerts."
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


@super_admin_only
def admin_payment_alerts(request):

    alerts = WorkerPaymentAlert.objects.select_related(
        "worker"
    ).order_by(
        "-created_at"
    )

    # -----------------------------------------------------
    # STATISTICS
    # -----------------------------------------------------

    total_alerts = WorkerPaymentAlert.objects.count()

    pending_followups = WorkerPaymentAlert.objects.filter(
        status__in=[
            "Pending",
            "Follow-up",
        ]
    ).count()

    sms_pending = WorkerPaymentAlert.objects.filter(
        sms_status="Pending"
    ).count()

    resolved_alerts = WorkerPaymentAlert.objects.filter(
        status="Resolved"
    ).count()

    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    return render(
        request,
        "admin_dashboard/payment_alerts.html",
        {
            "alerts": alerts,

            "total_alerts":
                total_alerts,

            "pending_followups":
                pending_followups,

            "sms_pending":
                sms_pending,

            "resolved_alerts":
                resolved_alerts,
        }
    )
    

# =========================================================
# PAYMENT ALERT DETAILS
# SUPER ADMIN ONLY
# =========================================================

@super_admin_only
def admin_payment_alert_detail(request, alert_id):

    alert = WorkerPaymentAlert.objects.select_related(
        "worker"
    ).get(
        id=alert_id
    )

    worker = alert.worker

    # -----------------------------------------------------
    # PENDING LEDGER ENTRIES
    # -----------------------------------------------------

    pending_ledger_entries = WorkerLedger.objects.filter(
        worker=worker,
        transaction_type="Booking Fee",
        status="Pending",
    ).select_related(
        "booking"
    ).order_by(
        "created_at"
    )

    # -----------------------------------------------------
    # CURRENT OUTSTANDING
    # -----------------------------------------------------

    outstanding_result = WorkerLedger.objects.filter(
        worker=worker,
        transaction_type="Booking Fee",
        status="Pending",
    ).aggregate(
        total=Sum("amount")
    )

    current_outstanding = (
        outstanding_result["total"] or 0
    )

    # -----------------------------------------------------
    # LAST BOOKING
    # -----------------------------------------------------

    last_booking = Booking.objects.filter(
        worker=worker
    ).order_by(
        "-created_at"
    ).first()

    # -----------------------------------------------------
    # LAST PAYMENT
    # -----------------------------------------------------

    last_payment = WorkerLedger.objects.filter(
        worker=worker,
        transaction_type="Payment",
        status="Paid",
    ).order_by(
        "-paid_at",
        "-created_at"
    ).first()

    # -----------------------------------------------------
    # ALERT HISTORY
    # -----------------------------------------------------

    alert_history = WorkerPaymentAlert.objects.filter(
        worker=worker
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "admin_dashboard/payment_alert_detail.html",
        {
            "alert": alert,
            "worker": worker,

            "pending_ledger_entries":
                pending_ledger_entries,

            "current_outstanding":
                current_outstanding,

            "last_booking":
                last_booking,

            "last_payment":
                last_payment,

            "alert_history":
                alert_history,
        }
    )
# =========================================================
# MARK PAYMENT ALERT FOLLOW-UP
# SUPER ADMIN ONLY
# =========================================================

@super_admin_only
def admin_payment_alert_follow_up(request, alert_id):

    if request.method != "POST":
        raise PermissionDenied(
            "Follow-up action must use POST."
        )

    alert = WorkerPaymentAlert.objects.get(
        id=alert_id
    )

    from payments.alert_service import mark_alert_follow_up

    mark_alert_follow_up(alert)

    return redirect(
        "admin_payment_alert_detail",
        alert_id=alert.id
    )


# =========================================================
# SEND PAYMENT ALERT SMS
# SUPER ADMIN ONLY
# =========================================================

@super_admin_only
def admin_payment_alert_send_sms(request, alert_id):

    if request.method != "POST":
        raise PermissionDenied(
            "SMS action must use POST."
        )

    alert = WorkerPaymentAlert.objects.get(
        id=alert_id
    )

    from payments.sms_service import send_alert_sms

    send_alert_sms(alert)

    return redirect(
        "admin_payment_alert_detail",
        alert_id=alert.id
    )

    
# =========================================================
# WORKER LEDGER
# SUPER ADMIN ONLY
# =========================================================

@super_admin_required
def admin_worker_ledger(request):

    ledger_entries = WorkerLedger.objects.select_related(
        "worker",
        "booking"
    ).order_by(
        "-created_at"
    )

    status_filter = request.GET.get("status")

    if status_filter in [
        "Pending",
        "Paid",
    ]:
        ledger_entries = ledger_entries.filter(
            status=status_filter
        )

    transaction_filter = request.GET.get("transaction")

    if transaction_filter in [
        "Booking Fee",
        "Payment",
    ]:
        ledger_entries = ledger_entries.filter(
            transaction_type=transaction_filter
        )

    # =====================================================
    # LEDGER SUMMARY
    # =====================================================

    total_ledger_amount = (
        WorkerLedger.objects.aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    pending_amount = (
        WorkerLedger.objects.filter(
            status="Pending"
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    paid_amount = (
        WorkerLedger.objects.filter(
            status="Paid"
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    return render(
        request,
        "admin_dashboard/worker_ledger.html",
        {
            "ledger_entries": ledger_entries,
            "status_filter": status_filter,
            "transaction_filter": transaction_filter,

            "total_ledger_amount":
                total_ledger_amount,

            "pending_amount":
                pending_amount,

            "paid_amount":
                paid_amount,
        }
    )


# =========================================================
# SUPER ADMIN ONLY
# ADMIN MANAGEMENT SECURITY
# =========================================================

def super_admin_required(view_func):
    """
    Allow ONLY Django Super Admin users.

    Normal Admin users are explicitly denied.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_superuser:
            raise PermissionDenied(
                "Only Super Admin can access Admin Management."
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# =========================================================
# ADMIN MANAGEMENT
# SUPER ADMIN ONLY
# =========================================================

@super_admin_required
def admin_management(request):

    # -----------------------------------------------------
    # ONLY NORMAL ADMINS
    #
    # Super Admin itself is not included in this list.
    # -----------------------------------------------------

    admins = User.objects.filter(
        is_staff=True,
        is_superuser=False
    ).prefetch_related(
        "groups",
        "user_permissions"
    ).order_by(
        "username"
    )

    # -----------------------------------------------------
    # ALL AVAILABLE GROUPS
    # -----------------------------------------------------

    groups = Group.objects.all().order_by(
        "name"
    )

    return render(
        request,
        "admin_dashboard/admin_management.html",
        {
            "admins": admins,
            "groups": groups,
        }
    )