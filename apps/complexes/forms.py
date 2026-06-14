from django import forms
from django.utils.text import slugify

from .models import Complex, Court, Schedule


class ComplexForm(forms.ModelForm):
    class Meta:
        model = Complex
        fields = [
            "name", "description", "address", "city",
            "province", "phone", "email", "logo", "cover",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "placeholder": "Ej: La Cantera Pádel Club",
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "rows": 3,
                "placeholder": "Descripción breve del complejo...",
            }),
            "address": forms.TextInput(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "placeholder": "Av. Siempre Viva 742",
            }),
            "city": forms.TextInput(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "placeholder": "Buenos Aires",
            }),
            "province": forms.TextInput(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "placeholder": "Buenos Aires",
            }),
            "phone": forms.TextInput(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "placeholder": "+54 11 1234-5678",
            }),
            "email": forms.EmailInput(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "placeholder": "info@complejo.com",
            }),
            "logo": forms.FileInput(attrs={
                "class": "w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100",
            }),
            "cover": forms.FileInput(attrs={
                "class": "w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100",
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance


class CourtForm(forms.ModelForm):
    class Meta:
        model = Court
        fields = [
            "name", "sport", "surface",
            "price_per_hour", "is_indoor", "is_active", "notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "placeholder": "Ej: Cancha 1",
            }),
            "sport": forms.Select(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
            }),
            "surface": forms.Select(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
            }),
            "price_per_hour": forms.NumberInput(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "placeholder": "0.00",
                "step": "0.01",
            }),
            "notes": forms.Textarea(attrs={
                "class": "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition",
                "rows": 2,
            }),
        }