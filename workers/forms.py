from django import forms
from django.contrib.auth.models import User
from .models import Worker


class WorkerRegistrationForm(forms.ModelForm):

    username = forms.CharField(max_length=150)

    password = forms.CharField(
        widget=forms.PasswordInput()
    )

    class Meta:
        model = Worker

        fields = [
            "name",
            "mobile",
            "profession",
            "experience",
            "city",
            "area",
            "daily_wage",
            "about",
            "profile_photo",
            "username",
            "password",
        ]