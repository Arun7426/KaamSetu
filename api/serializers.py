from rest_framework import serializers

from accounts.models import CustomerProfile
from workers.models import Worker



ROLE_CHOICES = [
    ("customer", "Customer"),
    ("worker", "Worker"),
]

OTP_PURPOSE_CHOICES = [
    ("registration", "Registration"),
    ("login", "Login"),
    ("website_login_setup", "Website Login Setup"),
]


class SendOTPSerializer(serializers.Serializer):

    mobile = serializers.CharField(
        max_length=10,
        min_length=10,
    )

    purpose = serializers.ChoiceField(
        choices=OTP_PURPOSE_CHOICES,
        default="registration",
    )

    role = serializers.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
    )

    def validate_mobile(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Mobile number must contain only digits."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "Enter a valid 10-digit mobile number."
            )

        return value

    def validate(self, attrs):
        purpose = attrs.get("purpose")
        role = attrs.get("role")

        if purpose == "registration" and not role:
            raise serializers.ValidationError({
                "role": "Role is required for registration."
            })

        return attrs


class VerifyOTPSerializer(serializers.Serializer):

    mobile = serializers.CharField(
        max_length=10,
        min_length=10,
    )

    otp = serializers.CharField(
        max_length=6,
        min_length=6,
    )

    purpose = serializers.ChoiceField(
        choices=OTP_PURPOSE_CHOICES,
        default="registration",
    )

    role = serializers.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
    )

    def validate_mobile(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Mobile number must contain only digits."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "Enter a valid 10-digit mobile number."
            )

        return value

    def validate_otp(self, value):
        value = value.strip()

        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError(
                "Enter a valid 6-digit OTP."
            )

        return value


class MobileRegistrationSerializer(serializers.Serializer):

    mobile = serializers.CharField(
        max_length=10,
        min_length=10,
    )

    role = serializers.ChoiceField(
        choices=ROLE_CHOICES,
    )

    name = serializers.CharField(
        max_length=100,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    address = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    profession = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=30,
    )

    experience = serializers.IntegerField(
        required=False,
        min_value=0,
    )

    city = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    area = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    daily_wage = serializers.DecimalField(
        required=False,
        max_digits=8,
        decimal_places=2,
        min_value=0,
    )

    about = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate_mobile(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Mobile number must contain only digits."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "Enter a valid 10-digit mobile number."
            )

        return value

    def validate(self, attrs):

        if attrs["role"] == "worker":

            required_worker_fields = [
                "profession",
                "experience",
                "city",
                "area",
                "daily_wage",
            ]

            missing = [
                field
                for field in required_worker_fields
                if attrs.get(field) in [None, ""]
            ]

            if missing:
                raise serializers.ValidationError({
                    field: "This field is required for workers."
                    for field in missing
                })

        return attrs


class WebsiteLoginSetupSerializer(serializers.Serializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
    )

    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
    )

    def validate(self, attrs):

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        return attrs


# =========================================================
# MODULE 2 — WORKER DISCOVERY / SEARCH
# =========================================================

class WorkerListSerializer(serializers.ModelSerializer):

    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = Worker
        fields = [
            "id",
            "name",
            "profession",
            "experience",
            "city",
            "area",
            "work_range",
            "daily_wage",
            "rating",
            "reviews",
            "available",
            "vverified",
            "profile_photo",
        ]

    def get_profile_photo(self, obj):

        if not obj.profile_photo:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                obj.profile_photo.url
            )

        return obj.profile_photo.url


class WorkerDetailSerializer(serializers.ModelSerializer):

    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = Worker
        fields = [
            "id",
            "name",
            "profession",
            "experience",
            "city",
            "area",
            "latitude",
            "longitude",
            "work_range",
            "daily_wage",
            "about",
            "available",
            "rating",
            "reviews",
            "vverified",
            "profile_photo",
        ]

    def get_profile_photo(self, obj):

        if not obj.profile_photo:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                obj.profile_photo.url
            )

        return obj.profile_photo.url


# =========================================================
# MODULE 3 — PROFILE API
# =========================================================

class CustomerProfileAPISerializer(serializers.Serializer):

    user_id = serializers.CharField(
        read_only=True
    )

    role = serializers.CharField(
        read_only=True
    )

    mobile = serializers.CharField(
        read_only=True
    )

    mobile_verified = serializers.BooleanField(
        read_only=True
    )

    name = serializers.CharField(
        max_length=100,
        required=False,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    address = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )


class WorkerProfileAPISerializer(serializers.Serializer):

    user_id = serializers.CharField(
        read_only=True
    )

    role = serializers.CharField(
        read_only=True
    )

    mobile = serializers.CharField(
        read_only=True
    )

    name = serializers.CharField(
        max_length=100,
        required=False,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    profession = serializers.ChoiceField(
        choices=Worker.PROFESSION_CHOICES,
        required=False,
    )

    experience = serializers.IntegerField(
        min_value=0,
        required=False,
    )

    city = serializers.CharField(
        max_length=100,
        required=False,
    )

    area = serializers.CharField(
        max_length=100,
        required=False,
    )

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    work_range = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        required=False,
    )

    daily_wage = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
        required=False,
    )

    about = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    available = serializers.BooleanField(
        required=False,
    )

    profile_photo = serializers.ImageField(
        required=False,
        allow_null=True,
    )

# =========================================================
# MODULE 4 — BOOKING API
# =========================================================

from bookings.models import Booking


class BookingCreateSerializer(serializers.Serializer):

    worker_id = serializers.IntegerField(
        min_value=1
    )

    customer_address = serializers.CharField(
        required=True,
        allow_blank=False
    )

    work_date = serializers.DateField(
        required=True
    )

    work_description = serializers.CharField(
        required=True,
        allow_blank=False
    )


class BookingSerializer(serializers.ModelSerializer):

    worker_id = serializers.IntegerField(
        source="worker.id",
        read_only=True
    )

    worker_name = serializers.CharField(
        source="worker.name",
        read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "worker_id",
            "worker_name",
            "customer_name",
            "customer_mobile",
            "customer_address",
            "work_date",
            "work_description",
            "status",
            "original_amount",
            "customer_offer",
            "worker_counter_offer",
            "final_amount",
            "negotiation_status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "worker_id",
            "worker_name",
            "customer_name",
            "customer_mobile",
            "status",
            "original_amount",
            "customer_offer",
            "worker_counter_offer",
            "final_amount",
            "negotiation_status",
            "created_at",
        ]

class CustomerOfferSerializer(serializers.Serializer):

    offer_amount = serializers.IntegerField(
        min_value=1,
        max_value=9999,
    )


class WorkerOfferResponseSerializer(serializers.Serializer):

    action = serializers.ChoiceField(
        choices=["accept", "counter"],
    )

    counter_amount = serializers.IntegerField(
        min_value=1,
        max_value=9999,
        required=False,
    )


class CustomerCounterResponseSerializer(serializers.Serializer):

    action = serializers.ChoiceField(
        choices=["accept", "reject"],
    )

class WorkerBookingStatusSerializer(serializers.Serializer):

    action = serializers.ChoiceField(
        choices=["accept", "reject", "complete"],
    )

class ReviewCreateSerializer(serializers.Serializer):

    rating = serializers.IntegerField(
        min_value=1,
        max_value=5,
    )

    comment = serializers.CharField(
        required=False,
        allow_blank=True,
    )