from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from payments.models import WorkerLedger, WorkerPaymentAlert


OUTSTANDING_LIMIT = Decimal("200.00")


def get_worker_outstanding(worker):
    """
    Return the worker's current pending Booking Fee outstanding.
    """

    total = (
        WorkerLedger.objects.filter(
            worker=worker,
            transaction_type="Booking Fee",
            status="Pending",
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
    )

    return total or Decimal("0.00")


def check_worker_payment_alert(worker):
    """
    Check the worker's current outstanding amount.

    Creates a new alert when the worker reaches
    the ₹200 threshold.

    If an active alert already exists, it is updated
    instead of creating a duplicate.
    """

    outstanding = get_worker_outstanding(worker)

    # -----------------------------------------------------
    # BELOW LIMIT
    # -----------------------------------------------------

    if outstanding < OUTSTANDING_LIMIT:

        resolve_worker_payment_alert(worker)

        return None

    # -----------------------------------------------------
    # EXISTING ACTIVE ALERT
    # -----------------------------------------------------

    existing_alert = WorkerPaymentAlert.objects.filter(
        worker=worker,
        alert_type="Outstanding Limit",
        status__in=[
            "Pending",
            "Follow-up",
        ],
    ).first()

    if existing_alert:

        update_fields = []

        if existing_alert.outstanding_amount != outstanding:

            existing_alert.outstanding_amount = outstanding

            update_fields.append(
                "outstanding_amount"
            )

        # If the alert was previously resolved and somehow
        # reused, make sure its resolved timestamp is cleared.
        if existing_alert.resolved_at is not None:

            existing_alert.resolved_at = None

            update_fields.append(
                "resolved_at"
            )

        if update_fields:

            update_fields.append("updated_at")

            existing_alert.save(
                update_fields=update_fields
            )

        return existing_alert

    # -----------------------------------------------------
    # CREATE NEW ALERT
    # -----------------------------------------------------

    alert = WorkerPaymentAlert.objects.create(

        worker=worker,

        alert_type="Outstanding Limit",

        outstanding_amount=outstanding,

        threshold_amount=OUTSTANDING_LIMIT,

        status="Pending",

        sms_status="Pending",
    )

    return alert


def resolve_worker_payment_alert(worker):
    """
    Resolve all active outstanding-limit alerts for the worker
    when the outstanding amount falls below the threshold.
    """

    active_alerts = WorkerPaymentAlert.objects.filter(
        worker=worker,
        alert_type="Outstanding Limit",
        status__in=[
            "Pending",
            "Follow-up",
        ],
    )

    if not active_alerts.exists():
        return

    active_alerts.update(
        status="Resolved",
        resolved_at=timezone.now(),
    )


def mark_alert_follow_up(alert):
    """
    Mark an active payment alert as followed up.
    """

    if alert.status == "Resolved":
        return alert

    alert.status = "Follow-up"
    alert.last_follow_up_at = timezone.now()

    alert.save(
        update_fields=[
            "status",
            "last_follow_up_at",
            "updated_at",
        ]
    )

    return alert