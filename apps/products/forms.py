from django import forms

from .models import Product, ProductCategory, Sale, SaleItem

INPUT_CLASS = (
    "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-primary-500 "
    "focus:border-transparent transition"
)


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "description", "price", "stock", "min_stock", "is_active"]
        widgets = {
            "category": forms.Select(attrs={"class": INPUT_CLASS}),
            "name": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Ej: Paleta Head Flash"}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2}),
            "price": forms.NumberInput(attrs={"class": INPUT_CLASS, "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "min_stock": forms.NumberInput(attrs={"class": INPUT_CLASS}),
        }

    def __init__(self, *args, complex=None, **kwargs):
        super().__init__(*args, **kwargs)
        if complex:
            self.fields["category"].queryset = ProductCategory.objects.filter(complex=complex)


class StockAdjustmentForm(forms.Form):
    quantity = forms.IntegerField(
        label="Cantidad",
        help_text="Positivo para entrada, negativo para salida.",
        widget=forms.NumberInput(attrs={"class": INPUT_CLASS}),
    )
    notes = forms.CharField(
        label="Notas",
        required=False,
        widget=forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2}),
    )


class SaleItemForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        label="Producto",
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Cantidad",
        widget=forms.NumberInput(attrs={"class": INPUT_CLASS}),
    )

    def __init__(self, *args, complex=None, **kwargs):
        super().__init__(*args, **kwargs)
        if complex:
            self.fields["product"].queryset = Product.objects.filter(
                complex=complex, is_active=True, stock__gt=0
            )