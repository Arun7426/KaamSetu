from django import forms
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control",
                "placeholder": field.label,
            })

        self.fields["about"].widget.attrs.update({
            "rows": 5,
            "placeholder": "Apne baare mein likhiye..."
        })

        self.fields["password"].widget.attrs.update({
            "placeholder": "Password"
        })

        self.fields["profile_photo"].widget.attrs.update({
            "class": "form-control-file"
        })

        # Profession Dropdown
        self.fields["profession"].choices = [
            ("", "Select Profession"),
            ("Electrician", "Electrician"),
            ("Plumber", "Plumber"),
            ("Carpenter", "Carpenter"),
            ("Painter", "Painter"),
            ("Mason", "Mason"),
            ("Cleaner", "Cleaner"),
            ("Welder", "Welder"),
            ("AC Technician", "AC Technician"),
            ("Mechanic", "Mechanic"),
            ("Driver", "Driver"),
            ("House Maid", "House Maid"),
            ("Cook", "Cook"),
            ("Gardener", "Gardener"),
            ("Labour", "Labour"),
            ("Tiles Worker", "Tiles Worker"),
            ("POP Worker", "POP Worker"),
            ("Other", "Other"),
        ]

# ==========================
# Worker Profile Edit Form
# ==========================

class WorkerProfileEditForm(forms.ModelForm):

    first_name = forms.CharField(
        max_length=100,
        required=True,
        label="Full Name",
    )

    email = forms.EmailField(
        required=False,
        label="Email Address",
    )

    class Meta:
        model = Worker

        fields = [
            "profession",
            "experience",
            "city",
            "area",
            "daily_wage",
            "about",
            "profile_photo",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Full Name
        self.fields["first_name"].widget = forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Full Name",
            }
        )

        # Email
        self.fields["email"].widget = forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email Address",
            }
        )

        # Profession
        self.fields["profession"].widget.attrs.update({
            "class": "form-control",
        })

        # Experience
        self.fields["experience"].widget.attrs.update({
            "class": "form-control",
            "min": "0",
        })

        # City
        self.fields["city"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "City",
        })

        # Area
        self.fields["area"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Area",
        })

        # Daily Wage
        self.fields["daily_wage"].widget.attrs.update({
            "class": "form-control",
            "min": "0",
        })

        # About
        self.fields["about"].widget = forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Apne baare mein likhiye...",
                "rows": 5,
            }
        )

        # Profile Photo
        self.fields["profile_photo"].widget.attrs.update({
            "class": "form-control-file",
        })