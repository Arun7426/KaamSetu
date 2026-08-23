from django.utils import timezone

from payments.models import WorkerPaymentAlert


def build_payment_alert_message(alert):
    """
    Build the SMS message for a worker payment alert.

    Provider integration is intentionally kept separate.
    """

    worker = alert.worker

    return (
        f"KaamSetu Payment Alert: "
        f"Your outstanding platform fee is ₹"
        f"{alert.outstanding_amount}. "
        f"Please make the payment to continue receiving new bookings."
    )


def send_sms_via_provider(mobile, message):
    """
    Provider adapter placeholder.

    Actual SMS provider integration will be added later.

    Returns:
        {
            "success": bool,
            "error": str | None
        }
    """

    # -------------------------------------------------
    # SMS PROVIDER WILL BE CONNECTED HERE LATER
    # -------------------------------------------------

    return {
        "success": False,
        "error": "SMS provider not configured."
    }


def send_alert_sms(alert):
    """
    Send an SMS for a WorkerPaymentAlert.

    This function manages the alert's SMS lifecycle.
    """

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------

    if not alert:
        return False

    if alert.status == "Resolved":
        return False

    worker = alert.worker

    mobile = worker.mobile

    if not mobile:
        alert.sms_status = "Failed"
        alert.sms_error = "Worker mobile number is missing."

        alert.save(
            update_fields=[
                "sms_status",
                "sms_error",
                "updated_at",
            ]
        )

        return False

    # -------------------------------------------------
    # BUILD MESSAGE
    # -------------------------------------------------

    message = build_payment_alert_message(
        alert
    )

    # -------------------------------------------------
    # MARK AS PENDING
    # -------------------------------------------------

    alert.sms_status = "Pending"
    alert.sms_error = ""

    alert.save(
        update_fields=[
            "sms_status",
            "sms_error",
            "updated_at",
        ]
    )

    # -------------------------------------------------
    # SEND THROUGH PROVIDER
    # -------------------------------------------------

    result = send_sms_via_provider(
        mobile,
        message
    )

    # -------------------------------------------------
    # SUCCESS
    # -------------------------------------------------

    if result.get("success"):

        alert.sms_status = "Sent"
        alert.sms_sent_at = timezone.now()
        alert.sms_error = ""

        alert.save(
            update_fields=[
                "sms_status",
                "sms_sent_at",
                "sms_error",
                "updated_at",
            ]
        )

        return True

    # -------------------------------------------------
    # FAILURE
    # -------------------------------------------------

    alert.sms_status = "Failed"
    alert.sms_error = (
        result.get("error")
        or "Unknown SMS provider error."
    )

    alert.save(
        update_fields=[
            "sms_status",
            "sms_error",
            "updated_at",
        ]
    )

    return False