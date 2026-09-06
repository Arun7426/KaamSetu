from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Sum, Q, Avg, Count
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from functools import wraps

from workers.models import Worker
from bookings.models import Booking, Review, Notification
from payments.models import WorkerLedger, WorkerPaymentAlert, FeeSetting, Promotion



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
# FEE SETTINGS
# SUPER ADMIN ONLY
# =========================================================

@super_admin_required
def admin_fee_settings(request):
    """
    Manage the single active platform fee configuration.

    Fee Settings are intentionally restricted to Super Admin.
    Existing FeeSetting model is reused; no migration is required.
    """

    fee_setting = FeeSetting.objects.first()

    # Create the default only when the table has no setting at all.
    # An intentionally inactive setting must remain inactive.
    if fee_setting is None:
        fee_setting = FeeSetting.objects.create(
            fee_type="fixed",
            fee_value=Decimal("20.00"),
            is_active=True,
        )

    if request.method == "POST":

        fee_type = request.POST.get("fee_type")
        fee_value_raw = request.POST.get("fee_value", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if fee_type not in {"fixed", "percentage"}:
            messages.error(request, "Please select a valid fee type.")
            return redirect("admin_fee_settings")

        try:
            fee_value = Decimal(fee_value_raw)
        except Exception:
            messages.error(request, "Please enter a valid fee value.")
            return redirect("admin_fee_settings")

        if fee_value < 0:
            messages.error(request, "Fee value cannot be negative.")
            return redirect("admin_fee_settings")

        if fee_type == "percentage" and fee_value > 100:
            messages.error(request, "Percentage fee cannot exceed 100%.")
            return redirect("admin_fee_settings")

        fee_setting.fee_type = fee_type
        fee_setting.fee_value = fee_value
        fee_setting.is_active = is_active
        fee_setting.save()

        messages.success(request, "Fee Settings updated successfully.")
        return redirect("admin_fee_settings")

    return render(
        request,
        "admin_dashboard/fee_settings.html",
        {"fee_setting": fee_setting},
    )



# =========================================================
# PROMOTION MANAGEMENT
# SUPER ADMIN ONLY
# =========================================================

@super_admin_required
def admin_promotions(request):
    """
    Manage KaamSetu promotions.

    Current Promotion model is intentionally reused without adding
    fields or migrations. Only Super Admin can create, edit, activate,
    deactivate, or delete promotions.

    The payment service currently uses the newest active promotion,
    so this view keeps at most one promotion active at a time.
    """

    promotions = Promotion.objects.order_by(
        "-is_active",
        "-updated_at",
        "-created_at",
    )

    return render(
        request,
        "admin_dashboard/promotions.html",
        {
            "promotions": promotions,
        }
    )


@super_admin_required
def admin_promotion_create(request):
    """Create a new promotion. Super Admin only."""

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        free_bookings_limit_raw = request.POST.get(
            "free_bookings_limit",
            ""
        ).strip()
        is_active = request.POST.get("is_active") == "on"

        if not name:
            messages.error(
                request,
                "Promotion name is required."
            )
            return redirect("admin_promotion_create")

        try:
            free_bookings_limit = int(free_bookings_limit_raw)
        except (TypeError, ValueError):
            messages.error(
                request,
                "Please enter a valid free booking limit."
            )
            return redirect("admin_promotion_create")

        if free_bookings_limit < 0:
            messages.error(
                request,
                "Free booking limit cannot be negative."
            )
            return redirect("admin_promotion_create")

        promotion = Promotion.objects.create(
            name=name,
            free_bookings_limit=free_bookings_limit,
            is_active=is_active,
        )

        # The current payment service selects the newest active
        # promotion. Keep only one active promotion at a time.
        if is_active:
            Promotion.objects.exclude(
                pk=promotion.pk
            ).update(
                is_active=False
            )

        messages.success(
            request,
            "Promotion created successfully."
        )

        return redirect("admin_promotions")

    return render(
        request,
        "admin_dashboard/promotion_form.html",
        {
            "page_title": "Create Promotion",
            "form_action": "admin_promotion_create",
            "promotion": None,
        }
    )


@super_admin_required
def admin_promotion_edit(request, promotion_id):
    """Edit an existing promotion. Super Admin only."""

    promotion = Promotion.objects.filter(
        id=promotion_id
    ).first()

    if promotion is None:
        raise PermissionDenied("Promotion not found.")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        free_bookings_limit_raw = request.POST.get(
            "free_bookings_limit",
            ""
        ).strip()
        is_active = request.POST.get("is_active") == "on"

        if not name:
            messages.error(
                request,
                "Promotion name is required."
            )
            return redirect(
                "admin_promotion_edit",
                promotion_id=promotion.id
            )

        try:
            free_bookings_limit = int(free_bookings_limit_raw)
        except (TypeError, ValueError):
            messages.error(
                request,
                "Please enter a valid free booking limit."
            )
            return redirect(
                "admin_promotion_edit",
                promotion_id=promotion.id
            )

        if free_bookings_limit < 0:
            messages.error(
                request,
                "Free booking limit cannot be negative."
            )
            return redirect(
                "admin_promotion_edit",
                promotion_id=promotion.id
            )

        promotion.name = name
        promotion.free_bookings_limit = free_bookings_limit
        promotion.is_active = is_active
        promotion.save()

        if is_active:
            Promotion.objects.exclude(
                pk=promotion.pk
            ).update(
                is_active=False
            )

        messages.success(
            request,
            "Promotion updated successfully."
        )

        return redirect("admin_promotions")

    return render(
        request,
        "admin_dashboard/promotion_form.html",
        {
            "page_title": "Edit Promotion",
            "form_action": "admin_promotion_edit",
            "promotion": promotion,
        }
    )


@super_admin_required
def admin_promotion_toggle(request, promotion_id):
    """Activate/deactivate a promotion. Super Admin only."""

    if request.method != "POST":
        return redirect("admin_promotions")

    promotion = Promotion.objects.filter(
        id=promotion_id
    ).first()

    if promotion is None:
        raise PermissionDenied("Promotion not found.")

    promotion.is_active = not promotion.is_active
    promotion.save(update_fields=["is_active", "updated_at"])

    if promotion.is_active:
        Promotion.objects.exclude(
            pk=promotion.pk
        ).update(
            is_active=False
        )
        messages.success(
            request,
            f'Promotion "{promotion.name}" is now active.'
        )
    else:
        messages.success(
            request,
            f'Promotion "{promotion.name}" is now inactive.'
        )

    return redirect("admin_promotions")


@super_admin_required
def admin_promotion_delete(request, promotion_id):
    """Delete a promotion. Super Admin only."""

    promotion = Promotion.objects.filter(
        id=promotion_id
    ).first()

    if promotion is None:
        raise PermissionDenied("Promotion not found.")

    if request.method == "POST":
        name = promotion.name
        promotion.delete()

        messages.success(
            request,
            f'Promotion "{name}" deleted successfully.'
        )

        return redirect("admin_promotions")

    return render(
        request,
        "admin_dashboard/promotion_delete.html",
        {
            "promotion": promotion,
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
# INSIGHTS & ANALYTICS
# =========================================================

@permission_required("bookings.view_booking")
def admin_insights(request):
    """
    KaamSetu Insights & Analytics.

    Supported periods:
        - daily
        - weekly
        - monthly
        - yearly
        - custom

    The selected period controls the operational and financial
    analytics shown on the Insights page. Current outstanding
    remains a live/global figure because it is not a historical
    period metric.

    Finance figures are intentionally available only to Super Admin.
    """

    # =====================================================
    # PERIOD / DATE FILTER
    # =====================================================

    today = timezone.localdate()

    period = request.GET.get("period", "monthly").lower()
    if period not in [
        "daily",
        "weekly",
        "monthly",
        "yearly",
        "custom",
    ]:
        period = "monthly"

    start_date = None
    end_date = today
    period_label = "Monthly"
    chart_granularity = "month"
    custom_start = request.GET.get("start_date", "")
    custom_end = request.GET.get("end_date", "")

    def subtract_months(year, month, count):
        total = (year * 12 + (month - 1)) - count
        return total // 12, (total % 12) + 1

    if period == "daily":
        # Last 30 days, shown day-by-day.
        start_date = today - timedelta(days=29)
        period_label = "Daily — Last 30 Days"
        chart_granularity = "day"

    elif period == "weekly":
        # Last 12 weeks, shown week-by-week.
        start_date = today - timedelta(days=83)
        period_label = "Weekly — Last 12 Weeks"
        chart_granularity = "week"

    elif period == "monthly":
        # Current month + previous 11 months.
        start_year, start_month = subtract_months(
            today.year,
            today.month,
            11
        )
        start_date = date(start_year, start_month, 1)
        period_label = "Monthly — Last 12 Months"
        chart_granularity = "month"

    elif period == "yearly":
        # Current year + previous 4 years.
        start_date = date(today.year - 4, 1, 1)
        period_label = "Yearly — Last 5 Years"
        chart_granularity = "year"

    else:
        # -------------------------------------------------
        # CUSTOM DATE RANGE
        # -------------------------------------------------
        try:
            parsed_start = date.fromisoformat(custom_start)
            parsed_end = date.fromisoformat(custom_end)

            if parsed_start > parsed_end:
                parsed_start, parsed_end = parsed_end, parsed_start

            start_date = parsed_start
            end_date = parsed_end
            period_label = (
                f"Custom — {start_date.strftime('%d %b %Y')}"
                f" to {end_date.strftime('%d %b %Y')}"
            )

        except (TypeError, ValueError):
            # Safe fallback if custom dates are missing/invalid.
            period = "monthly"
            start_year, start_month = subtract_months(
                today.year,
                today.month,
                11
            )
            start_date = date(start_year, start_month, 1)
            end_date = today
            period_label = "Monthly — Last 12 Months"
            chart_granularity = "month"

        if period == "custom":
            span_days = (end_date - start_date).days + 1

            # Keep custom charts readable automatically.
            if span_days <= 31:
                chart_granularity = "day"
            elif span_days <= 180:
                chart_granularity = "week"
            else:
                chart_granularity = "month"

    # =====================================================
    # BASE QUERYSETS FOR SELECTED PERIOD
    # =====================================================

    period_bookings = Booking.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    period_users = User.objects.filter(
        date_joined__date__gte=start_date,
        date_joined__date__lte=end_date,
    )

    period_reviews = Review.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    # =====================================================
    # GLOBAL USER TOTALS
    # =====================================================

    total_users = User.objects.count()
    total_workers = Worker.objects.count()
    total_customers = User.objects.filter(
        is_staff=False,
        worker_profile__isnull=True,
    ).count()

    # =====================================================
    # PERIOD USER GROWTH
    # =====================================================

    new_users = period_users.count()

    new_workers = period_users.filter(
        worker_profile__isnull=False,
    ).count()

    new_customers = period_users.filter(
        is_staff=False,
        worker_profile__isnull=True,
    ).count()

    # =====================================================
    # PERIOD BOOKING STATISTICS
    # =====================================================

    total_bookings = period_bookings.count()

    pending_bookings = period_bookings.filter(
        status="Pending"
    ).count()

    accepted_bookings = period_bookings.filter(
        status="Accepted"
    ).count()

    completed_bookings = period_bookings.filter(
        status="Completed"
    ).count()

    cancelled_bookings = period_bookings.filter(
        status="Cancelled"
    ).count()

    completion_rate = round(
        (completed_bookings / total_bookings) * 100,
        1
    ) if total_bookings else 0

    cancellation_rate = round(
        (cancelled_bookings / total_bookings) * 100,
        1
    ) if total_bookings else 0

    # =====================================================
    # PERIOD REVIEW / RATING STATISTICS
    # =====================================================

    review_stats = period_reviews.aggregate(
        total=Count("id"),
        average=Avg("rating"),
    )

    total_reviews = review_stats["total"] or 0
    average_rating = review_stats["average"] or 0
    average_rating = round(float(average_rating), 1)

    five_star_reviews = period_reviews.filter(
        rating=5
    ).count()

    low_rating_reviews = period_reviews.filter(
        rating__lte=2
    ).count()

    # =====================================================
    # TREND BUCKETS
    # =====================================================

    trend_labels = []
    trend_booking_counts = []
    trend_pending_counts = []
    trend_accepted_counts = []
    trend_completed_counts = []
    trend_cancelled_counts = []
    trend_user_counts = []

    # Finance trend data (Super Admin only)
    finance_platform_fee_counts = []
    finance_received_payment_counts = []

    buckets = []

    if chart_granularity == "day":
        current = start_date
        while current <= end_date:
            buckets.append((current, current))
            current += timedelta(days=1)

    elif chart_granularity == "week":
        current = start_date - timedelta(
            days=start_date.weekday()
        )
        last = end_date

        while current <= last:
            bucket_end = current + timedelta(days=6)
            buckets.append((current, bucket_end))
            current += timedelta(days=7)

    elif chart_granularity == "month":
        current_year = start_date.year
        current_month = start_date.month

        while True:
            bucket_start = date(
                current_year,
                current_month,
                1
            )

            if current_month == 12:
                next_month = date(
                    current_year + 1,
                    1,
                    1
                )
            else:
                next_month = date(
                    current_year,
                    current_month + 1,
                    1
                )

            bucket_end = next_month - timedelta(days=1)
            buckets.append((bucket_start, bucket_end))

            if bucket_end >= end_date:
                break

            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

    else:
        for current_year in range(
            start_date.year,
            end_date.year + 1
        ):
            bucket_start = date(current_year, 1, 1)
            bucket_end = date(current_year, 12, 31)
            buckets.append((bucket_start, bucket_end))

    for bucket_start, bucket_end in buckets:
        actual_start = max(bucket_start, start_date)
        actual_end = min(bucket_end, end_date)

        bucket_bookings = Booking.objects.filter(
            created_at__date__gte=actual_start,
            created_at__date__lte=actual_end,
        )

        bucket_users = User.objects.filter(
            date_joined__date__gte=actual_start,
            date_joined__date__lte=actual_end,
        )

        if chart_granularity == "day":
            label = bucket_start.strftime("%d %b")
        elif chart_granularity == "week":
            label = (
                f"{actual_start.strftime('%d %b')}"
                f" – {actual_end.strftime('%d %b')}"
            )
        elif chart_granularity == "month":
            label = bucket_start.strftime("%b %Y")
        else:
            label = bucket_start.strftime("%Y")

        trend_labels.append(label)
        trend_booking_counts.append(bucket_bookings.count())
        trend_pending_counts.append(
            bucket_bookings.filter(status="Pending").count()
        )
        trend_accepted_counts.append(
            bucket_bookings.filter(status="Accepted").count()
        )
        trend_completed_counts.append(
            bucket_bookings.filter(status="Completed").count()
        )
        trend_cancelled_counts.append(
            bucket_bookings.filter(status="Cancelled").count()
        )
        trend_user_counts.append(bucket_users.count())

        # -------------------------------------------------
        # FINANCE TREND (SUPER ADMIN ONLY)
        # -------------------------------------------------
        if request.user.is_superuser:
            bucket_platform_fees = WorkerLedger.objects.filter(
                transaction_type="Booking Fee",
                created_at__date__gte=actual_start,
                created_at__date__lte=actual_end,
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")

            bucket_received_payments = WorkerLedger.objects.filter(
                transaction_type="Payment",
                status="Paid",
                paid_at__date__gte=actual_start,
                paid_at__date__lte=actual_end,
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")

            finance_platform_fee_counts.append(
                float(bucket_platform_fees)
            )
            finance_received_payment_counts.append(
                float(bucket_received_payments)
            )

    # =====================================================
    # BOOKING STATUS DISTRIBUTION
    # =====================================================

    status_labels = [
        "Pending",
        "Accepted",
        "Completed",
        "Cancelled",
    ]

    status_counts = [
        pending_bookings,
        accepted_bookings,
        completed_bookings,
        cancelled_bookings,
    ]

    # =====================================================
    # FINANCE
    # SUPER ADMIN ONLY
    # =====================================================

    total_outstanding = None
    total_paid = None
    total_platform_fees = None

    period_platform_fees = None
    period_received_payments = None
    period_pending_fees = None
    period_paid_fees = None
    workers_with_outstanding = Worker.objects.none()
    period_ledger_entries = WorkerLedger.objects.none()

    if request.user.is_superuser:
        # -------------------------------------------------
        # LIVE / GLOBAL FINANCE
        # -------------------------------------------------

        total_outstanding = (
            WorkerLedger.objects.filter(
                transaction_type="Booking Fee",
                status="Pending",
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
        )

        total_paid = (
            WorkerLedger.objects.filter(
                transaction_type="Booking Fee",
                status="Paid",
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
        )

        total_platform_fees = (
            WorkerLedger.objects.filter(
                transaction_type="Booking Fee",
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
        )

        # -------------------------------------------------
        # SELECTED PERIOD FINANCE
        # -------------------------------------------------

        period_booking_fees = WorkerLedger.objects.filter(
            transaction_type="Booking Fee",
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )

        period_platform_fees = (
            period_booking_fees.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
        )

        period_pending_fees = (
            period_booking_fees.filter(
                status="Pending"
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
        )

        period_paid_fees = (
            period_booking_fees.filter(
                status="Paid"
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
        )

        # Payment transactions represent actual worker payments received.
        period_received_payments = (
            WorkerLedger.objects.filter(
                transaction_type="Payment",
                status="Paid",
                paid_at__date__gte=start_date,
                paid_at__date__lte=end_date,
            ).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")
        )

        # -------------------------------------------------
        # WORKER-WISE LIVE OUTSTANDING
        # -------------------------------------------------

        workers_with_outstanding = Worker.objects.annotate(
            outstanding=Sum(
                "ledger_entries__amount",
                filter=Q(
                    ledger_entries__transaction_type="Booking Fee",
                    ledger_entries__status="Pending",
                )
            )
        ).filter(
            outstanding__gt=0
        ).order_by(
            "-outstanding",
            "name",
        )

        # -------------------------------------------------
        # PERIOD LEDGER ACTIVITY
        # -------------------------------------------------

        period_ledger_entries = WorkerLedger.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).select_related(
            "worker",
            "booking",
        ).order_by(
            "-created_at"
        )[:20]

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {
        # ---------------------------------------------
        # PERIOD / FILTER
        # ---------------------------------------------
        "selected_period": period,
        "period_label": period_label,
        "start_date": start_date,
        "end_date": end_date,
        "custom_start": custom_start,
        "custom_end": custom_end,

        # ---------------------------------------------
        # GLOBAL USER TOTALS
        # ---------------------------------------------
        "total_users": total_users,
        "total_workers": total_workers,
        "total_customers": total_customers,

        # ---------------------------------------------
        # PERIOD USER GROWTH
        # ---------------------------------------------
        "new_users": new_users,
        "new_workers": new_workers,
        "new_customers": new_customers,

        # ---------------------------------------------
        # PERIOD BOOKING STATISTICS
        # ---------------------------------------------
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "accepted_bookings": accepted_bookings,
        "completed_bookings": completed_bookings,
        "cancelled_bookings": cancelled_bookings,
        "completion_rate": completion_rate,
        "cancellation_rate": cancellation_rate,

        # ---------------------------------------------
        # PERIOD REVIEWS
        # ---------------------------------------------
        "total_reviews": total_reviews,
        "average_rating": average_rating,
        "five_star_reviews": five_star_reviews,
        "low_rating_reviews": low_rating_reviews,

        # ---------------------------------------------
        # MAIN TREND CHART
        # ---------------------------------------------
        "chart_granularity": chart_granularity,
        "trend_labels": trend_labels,
        "trend_booking_counts": trend_booking_counts,
        "trend_pending_counts": trend_pending_counts,
        "trend_accepted_counts": trend_accepted_counts,
        "trend_completed_counts": trend_completed_counts,
        "trend_cancelled_counts": trend_cancelled_counts,
        "trend_user_counts": trend_user_counts,

        # ---------------------------------------------
        # FINANCE TREND CHART
        # ---------------------------------------------
        "finance_platform_fee_counts": finance_platform_fee_counts,
        "finance_received_payment_counts": finance_received_payment_counts,

        # ---------------------------------------------
        # STATUS CHART
        # ---------------------------------------------
        "status_labels": status_labels,
        "status_counts": status_counts,

        # ---------------------------------------------
        # FINANCE - SUPER ADMIN ONLY
        # ---------------------------------------------
        "total_outstanding": total_outstanding,
        "total_paid": total_paid,
        "total_platform_fees": total_platform_fees,
        "period_platform_fees": period_platform_fees,
        "period_received_payments": period_received_payments,
        "period_pending_fees": period_pending_fees,
        "period_paid_fees": period_paid_fees,
        "workers_with_outstanding": workers_with_outstanding,
        "period_ledger_entries": period_ledger_entries,
    }

    return render(
        request,
        "admin_dashboard/insights.html",
        context,
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