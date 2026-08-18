from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import CustomerProfile


class CustomerRegistrationForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=100,
        required=True,
    )

    email = forms.EmailField(
        required=True,
    )

    mobile = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "username",
            "email",
            "mobile",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["first_name"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Full Name",
        })

        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Username",
        })

        self.fields["email"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Email Address",
        })

        self.fields["mobile"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Mobile Number",
            "maxlength": "10",
            "minlength": "10",
            "pattern": "[0-9]{10}",
            "inputmode": "numeric",
        })

        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Password",
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm Password",
        })

        # Remove Django default help text
        self.fields["username"].help_text = ""
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""

        # Better labels
        self.fields["first_name"].label = "Full Name"
        self.fields["username"].label = "Username"
        self.fields["email"].label = "Email Address"
        self.fields["mobile"].label = "Mobile Number"
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm Password"

    def clean_mobile(self):

        mobile = self.cleaned_data.get("mobile", "").strip()

        if not mobile.isdigit():
            raise forms.ValidationError(
                "Mobile number must contain only digits."
            )

        if len(mobile) != 10:
            raise forms.ValidationError(
                "Enter a valid 10-digit mobile number."
            )

        if CustomerProfile.objects.filter(mobile=mobile).exists():
            raise forms.ValidationError(
                "This mobile number is already registered."
            )

        return mobile

# ==========================
# Customer Profile Edit Form
# ==========================

class CustomerProfileEditForm(forms.ModelForm):

    first_name = forms.CharField(
        max_length=100,
        required=True,
        label="Full Name",
    )

    email = forms.EmailField(
        required=True,
        label="Email Address",
    )

    class Meta:
        model = CustomerProfile
        fields = [
            "mobile",
            "address",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["first_name"].widget = forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Full Name",
            }
        )

        self.fields["email"].widget = forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email Address",
            }
        )

        self.fields["mobile"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Mobile Number",
            "maxlength": "10",
            "minlength": "10",
            "inputmode": "numeric",
        })

        self.fields["address"].widget = forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your address (Optional)",
                "rows": 3,
            }
        )

        self.fields["mobile"].label = "Mobile Number"
        self.fields["address"].label = "Address (Optional)"

        # Address optional
        self.fields["address"].required = False

        # Mobile अभी direct edit नहीं होगा
        self.fields["mobile"].required = True

    def clean_mobile(self):

        mobile = self.cleaned_data.get("mobile", "").strip()

        if not mobile.isdigit():

            raise forms.ValidationError(
                "Mobile number must contain only digits."
            )

        if len(mobile) != 10:

            raise forms.ValidationError(
                "Enter a valid 10-digit mobile number."
            )

        existing = CustomerProfile.objects.filter(
            mobile=mobile
        ).exclude(
            pk=self.instance.pk
        ).exists()

        if existing:

            raise forms.ValidationError(
                "This mobile number is already registered."
            )

        return mobile