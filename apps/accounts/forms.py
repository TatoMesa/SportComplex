from django import forms
from django.contrib.auth import get_user_model

from .models import Profile

User = get_user_model()

INPUT_CLASS = (
    "w-full rounded-xl border border-gray-200 dark:border-gray-700 "
    "bg-white dark:bg-gray-800 text-gray-900 dark:text-white "
    "px-4 py-2.5 text-sm focus:outline-none focus:ring-2 "
    "focus:ring-brand-500 focus:border-transparent transition"
)


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": INPUT_CLASS,
                "placeholder": "Juan",
            }),
            "last_name": forms.TextInput(attrs={
                "class": INPUT_CLASS,
                "placeholder": "García",
            }),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone", "bio", "birth_date", "avatar"]
        widgets = {
            "phone": forms.TextInput(attrs={
                "class": INPUT_CLASS,
                "placeholder": "+54 11 1234-5678",
            }),
            "bio": forms.Textarea(attrs={
                "class": INPUT_CLASS,
                "rows": 3,
                "placeholder": "Contá algo sobre vos...",
            }),
            "birth_date": forms.DateInput(
                attrs={"class": INPUT_CLASS, "type": "date"},
                format="%Y-%m-%d",
            ),
            "avatar": forms.FileInput(attrs={
                "class": "w-full text-sm text-gray-500 dark:text-gray-400 "
                         "file:mr-4 file:py-2 file:px-4 file:rounded-xl "
                         "file:border-0 file:text-sm file:font-semibold "
                         "file:bg-brand-50 file:text-brand-700 "
                         "hover:file:bg-brand-100 transition",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].input_formats = ["%Y-%m-%d"]