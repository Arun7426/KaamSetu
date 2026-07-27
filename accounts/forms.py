from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class CustomerRegistrationForm(UserCreationForm):

    first_name = forms.CharField(max_length=100)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "username",
            "email",
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

        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Password",
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm Password",
        })