from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db import models

from .models import WorkerLedger, FeeSetting, Promotion




def get_fee_setting():
    """
    Get the active platform fee setting.
    If no setting exists, create the default ₹20 fixed fee.
    """

    setting = FeeSetting.objects.filter(
        is_active=True
    ).first()

    if not setting:
        setting = FeeSetting.objects.create(
            fee_type="fixed",
            fee_value=Decimal("20.00"),
            is_active=True
        )

    return setting


def get_active_promotion():
    """
    Return the currently active promotion.
    """

    return Promotion.objects.filter(
        is_active=True
    ).order_by(
        "-created_at"
    ).first()


def calculate_platform_fee(booking):
    """
    Calculate the platform fee for a final accepted booking.
    """

    setting = get_fee_setting()

    if setting.fee_type == "fixed":
        return setting.fee_value

    if setting.fee_type == "percentage":

        if not booking.final_amount:
            return Decimal("0.00")

        fee = (
            Decimal(booking.final_amount)
            * setting.fee_value
            / Decimal("100")
        )

        return fee.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    return Decimal("0.00")


@transaction.atomic
def create_booking_fee(booking):
    """
    Create the KaamSetu platform fee after final acceptance.

    Active promotion can waive the fee for the first
    N final accepted bookings of each worker.
    """

    # -----------------------------------------
    # Prevent duplicate fee for same booking
    # -----------------------------------------

    existing_entry = WorkerLedger.objects.filter(
        booking=booking,
        transaction_type="Booking Fee"
    ).first()

    if existing_entry:
        return existing_entry


    # -----------------------------------------
    # Check active promotion
    # -----------------------------------------

    promotion = get_active_promotion()

    if promotion:

        successful_bookings = booking.__class__.objects.filter(
            worker=booking.worker,
            negotiation_status="Accepted"
        ).exclude(
            id=booking.id
        ).count()

        if successful_bookings < promotion.free_bookings_limit:

            return None


    # -----------------------------------------
    # Calculate actual platform fee
    # -----------------------------------------

    fee_amount = calculate_platform_fee(
        booking
    )

    if fee_amount <= 0:
        return None


    # -----------------------------------------
    # Create ledger entry
    # -----------------------------------------

    ledger_entry = WorkerLedger.objects.create(
        worker=booking.worker,
        booking=booking,
        transaction_type="Booking Fee",
        amount=fee_amount,
        status="Pending",
        description="KaamSetu platform booking fee"
    )

    return ledger_entry


def get_worker_outstanding(worker):
    """
    Return the worker's current unpaid platform fee.
    """

    outstanding = WorkerLedger.objects.filter(
        worker=worker,
        transaction_type="Booking Fee",
        status="Pending"
    ).aggregate(
        total=models.Sum("amount")
    )["total"]

    return outstanding or Decimal("0.00")

BOOKING_BLOCK_LIMIT = Decimal("200.00")


def can_worker_receive_booking(worker):
    """
    Check whether the worker is allowed to receive new bookings.
    """

    outstanding = get_worker_outstanding(worker)

    return outstanding < BOOKING_BLOCK_LIMIT

@transaction.atomic
def settle_worker_payment(worker, amount):
    """
    Settle the worker's outstanding platform fees.

    Payment is applied to the oldest pending booking fees first.
    """

    amount = Decimal(amount)

    if amount <= 0:
        return False

    pending_entries = WorkerLedger.objects.filter(
        worker=worker,
        transaction_type="Booking Fee",
        status="Pending"
    ).order_by(
        "created_at"
    )

    remaining_amount = amount

    for entry in pending_entries:

        if remaining_amount <= 0:
            break

        if remaining_amount >= entry.amount:

            remaining_amount -= entry.amount

            entry.status = "Paid"
            entry.paid_at = timezone.now()

            entry.save(
                update_fields=[
                    "status",
                    "paid_at"
                ]
            )

        else:
            # Partial payment will be handled later
            break

    return True