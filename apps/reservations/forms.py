from django import forms
from django.utils import timezone

from apps.complexes.models import Court
from .models import Payment, Reservation

INPUT_CLASS = (
    "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-primary-500 "
    "focus:border-transparent transition"
)

# Horas en punto de 06:00 a 24:00
HOUR_CHOICES = [("", "— Hora —")] + [
    (f"{h:02d}:00", f"{h:02d}:00") for h in range(6, 25)
]


class ReservationForm(forms.ModelForm):
    start_time = forms.ChoiceField(
        choices=HOUR_CHOICES,
        label="Hora inicio",
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )
    end_time = forms.ChoiceField(
        choices=HOUR_CHOICES,
        label="Hora fin",
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )

    class Meta:
        model = Reservation
        fields = ["court", "date", "start_time", "end_time", "notes"]
        widgets = {
            "court": forms.Select(attrs={"class": INPUT_CLASS}),
            "date": forms.DateInput(
                attrs={"class": INPUT_CLASS, "type": "date"},
                format="%Y-%m-%d",
            ),
            "notes": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2}),
        }

    def __init__(self, *args, complex=None, initial_data=None, **kwargs):
        super().__init__(*args, **kwargs)
        if complex:
            self.fields["court"].queryset = Court.objects.filter(
                complex=complex, is_active=True
            )
        self.fields["date"].input_formats = ["%Y-%m-%d"]

        # Prellenar desde parámetros GET
        if initial_data:
            if initial_data.get("court"):
                self.fields["court"].initial = initial_data["court"]
            if initial_data.get("date"):
                self.fields["date"].initial = initial_data["date"]
            if initial_data.get("start_time"):
                self.fields["start_time"].initial = initial_data["start_time"]
            if initial_data.get("end_time"):
                self.fields["end_time"].initial = initial_data["end_time"]
        
        # Si estamos editando, preseleccionar los valores actuales
        if self.instance and self.instance.pk:
            if self.instance.start_time:
                self.fields["start_time"].initial = (
                    self.instance.start_time.strftime("%H:%M")
                )
            if self.instance.end_time:
                self.fields["end_time"].initial = (
                    self.instance.end_time.strftime("%H:%M")
                )

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date and date < timezone.localdate():
            raise forms.ValidationError("No podés reservar en una fecha pasada.")
        return date

    def clean_start_time(self):
        value = self.cleaned_data.get("start_time")
        if not value:
            raise forms.ValidationError("Seleccioná la hora de inicio.")
        from datetime import time
        hour = int(value.split(":")[0])
        return time(hour, 0)

    def clean_end_time(self):
        value = self.cleaned_data.get("end_time")
        if not value:
            raise forms.ValidationError("Seleccioná la hora de fin.")
        from datetime import time
        hour = int(value.split(":")[0])
        # 24:00 lo convertimos a 23:59 para que sea válido como time
        if hour == 24:
            return time(23, 59)
        return time(hour, 0)

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and start >= end:
            raise forms.ValidationError(
                "La hora de inicio debe ser anterior a la hora de fin."
            )
        return cleaned


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "method", "notes"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASS, "step": "0.01"}),
            "method": forms.Select(attrs={"class": INPUT_CLASS}),
            "notes": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2}),
        }