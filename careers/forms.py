from django import forms

from .models import Application, Vacancy


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application

        fields = [
            "full_name",
            "email",
            "mobile",
            "education",
            "experience",
            "cover_letter",
            "cv",
        ]

        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "placeholder": "Full Name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Email Address",
                }
            ),
            "mobile": forms.TextInput(
                attrs={
                    "placeholder": "10-digit Mobile Number",
                    "inputmode": "numeric",
                    "autocomplete": "tel",
                    "maxlength": "10",
                    "minlength": "10",
                    "pattern": "[0-9]{10}",
                    "oninput": (
                        "this.value = this.value.replace(/\\D/g, '').slice(0, 10)"
                    ),
                }
            ),
            "education": forms.TextInput(
                attrs={
                    "placeholder": "Education / Qualification",
                }
            ),
            "experience": forms.TextInput(
                attrs={
                    "placeholder": "Experience (if any)",
                }
            ),
            "cover_letter": forms.Textarea(
                attrs={
                    "placeholder": "Tell us briefly about yourself and why you want to join KaamSetu.",
                    "rows": 5,
                }
            ),
            "cv": forms.ClearableFileInput(
                attrs={
                    "accept": ".pdf,.doc,.docx",
                }
            ),
        }

    def clean_mobile(self):
        mobile = self.cleaned_data["mobile"].strip()

        if not mobile.isdigit():
            raise forms.ValidationError(
                "Please enter a valid mobile number."
            )

        if len(mobile) != 10:
            raise forms.ValidationError(
                "Mobile number must be 10 digits."
            )

        return mobile

    def clean_cv(self):
        cv = self.cleaned_data.get("cv")

        if not cv:
            raise forms.ValidationError(
                "Please upload your CV / Resume."
            )

        allowed_extensions = [".pdf", ".doc", ".docx"]

        file_name = cv.name.lower()

        if not any(
            file_name.endswith(extension)
            for extension in allowed_extensions
        ):
            raise forms.ValidationError(
                "Only PDF, DOC, or DOCX files are allowed."
            )

        # 5 MB maximum
        if cv.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "CV / Resume size must not exceed 5 MB."
            )

        return cv


class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy

        fields = [
            "title",
            "short_description",
            "description",
            "eligibility",
            "location",
            "internship_type",
            "stipend",
            "openings",
            "application_deadline",
            "is_active",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Opportunity / Internship Title"
                }
            ),
            "short_description": forms.TextInput(
                attrs={
                    "placeholder": "Short Description"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Detailed opportunity description",
                    "rows": 6,
                }
            ),
            "eligibility": forms.Textarea(
                attrs={
                    "placeholder": "Eligibility / Requirements",
                    "rows": 5,
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "placeholder": "Location"
                }
            ),
            "internship_type": forms.TextInput(
                attrs={
                    "placeholder": "Volunteer Internship"
                }
            ),
            "stipend": forms.TextInput(
                attrs={
                    "placeholder": "Stipend (if any)"
                }
            ),
            "openings": forms.NumberInput(
                attrs={
                    "min": 1
                }
            ),
            "application_deadline": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),
        }