import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from .models import MobileOTP


OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


def normalize_mobile(mobile: str) -> str:
    """
    Normalize and validate a 10-digit Indian mobile number.
    """
    mobile = (mobile or "").strip()

    if not mobile.isdigit() or len(mobile) != 10:
        raise ValueError(
            "Enter a valid 10-digit mobile number."
        )

    return mobile


def hash_otp(otp: str) -> str:
    """
    Store only a SHA-256 hash of the OTP.
    """
    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def generate_otp() -> str:
    """
    Generate a secure 6-digit OTP.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


def create_mobile_otp(
    mobile: str,
    purpose: str = "registration",
    role: str = "customer",
) -> tuple[MobileOTP, str]:

    mobile = normalize_mobile(mobile)

    if purpose not in dict(MobileOTP.PURPOSE_CHOICES):
        raise ValueError("Invalid OTP purpose.")

    if role not in dict(MobileOTP.ROLE_CHOICES):
        raise ValueError("Invalid role.")

    # Invalidate previous active OTPs.
    MobileOTP.objects.filter(
        mobile=mobile,
        purpose=purpose,
        role=role,
        is_verified=False,
        consumed_at__isnull=True,
    ).update(
        consumed_at=timezone.now()
    )

    otp = generate_otp()

    otp_record = MobileOTP.objects.create(
        mobile=mobile,
        role=role,
        otp_hash=hash_otp(otp),
        purpose=purpose,
        expires_at=(
            timezone.now()
            + timedelta(minutes=OTP_EXPIRY_MINUTES)
        ),
    )

    return otp_record, otp


def verify_mobile_otp(
    mobile: str,
    otp: str,
    purpose: str = "registration",
    role: str | None = None,
) -> MobileOTP:

    mobile = normalize_mobile(mobile)
    otp = (otp or "").strip()

    if not otp.isdigit() or len(otp) != OTP_LENGTH:
        raise ValueError(
            "Enter a valid 6-digit OTP."
        )

    otp_query = MobileOTP.objects.filter(
        mobile=mobile,
        purpose=purpose,
        is_verified=False,
        consumed_at__isnull=True,
    )

    if role:
        otp_query = otp_query.filter(
            role=role
        )

    otp_record = (
        otp_query
        .order_by("-created_at")
        .first()
    )

    if otp_record is None:
        raise ValueError(
            "No active OTP found. Please request a new OTP."
        )

    if otp_record.is_expired():
        otp_record.consumed_at = timezone.now()
        otp_record.save(
            update_fields=["consumed_at"]
        )

        raise ValueError(
            "OTP has expired. Please request a new OTP."
        )

    if otp_record.attempts >= MAX_OTP_ATTEMPTS:
        otp_record.consumed_at = timezone.now()
        otp_record.save(
            update_fields=["consumed_at"]
        )

        raise ValueError(
            "Maximum OTP attempts exceeded. "
            "Please request a new OTP."
        )

    if not secrets.compare_digest(
        otp_record.otp_hash,
        hash_otp(otp),
    ):
        otp_record.attempts += 1

        if otp_record.attempts >= MAX_OTP_ATTEMPTS:
            otp_record.consumed_at = timezone.now()

            otp_record.save(
                update_fields=[
                    "attempts",
                    "consumed_at",
                ]
            )

            raise ValueError(
                "Maximum OTP attempts exceeded. "
                "Please request a new OTP."
            )

        otp_record.save(
            update_fields=["attempts"]
        )

        remaining = (
            MAX_OTP_ATTEMPTS
            - otp_record.attempts
        )

        raise ValueError(
            f"Invalid OTP. {remaining} attempt(s) remaining."
        )

    otp_record.is_verified = True
    otp_record.verified_at = timezone.now()

    otp_record.save(
        update_fields=[
            "is_verified",
            "verified_at",
        ]
    )

    return otp_record