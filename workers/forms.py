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