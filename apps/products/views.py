from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.complexes.models import Complex
from .forms import ProductCategoryForm, ProductForm, StockAdjustmentForm, SaleItemForm
from .models import Product, ProductCategory, Sale, SaleItem, StockMovement, StockMovementType

class ProductSelectComplexView(LoginRequiredMixin, ListView):
    """Si el admin tiene un solo complejo va directo, si tiene varios elige."""
    template_name = "products/select_complex.html"
    context_object_name = "complexes"

    def get_queryset(self):
        user = self.request.user
        from apps.complexes.models import Complex
        if user.is_super_admin:
            return Complex.objects.all()
        return Complex.objects.filter(owner=user)

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if qs.count() == 1:
            return redirect("products:complex_list", slug=qs.first().slug)
        return super().get(request, *args, **kwargs)

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "products/list.html"
    context_object_name = "products"

    def dispatch(self, request, *args, **kwargs):
        self.complex = get_object_or_404(Complex, slug=kwargs["slug"])
        if not request.user.is_super_admin and self.complex.owner != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Product.objects.filter(
            complex=self.complex
        ).select_related("category").order_by("category__name", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["complex"] = self.complex
        ctx["low_stock"] = [p for p in ctx["products"] if p.is_low_stock]
        return ctx


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/form.html"

    def dispatch(self, request, *args, **kwargs):
        self.complex = get_object_or_404(Complex, slug=kwargs["slug"])
        if not request.user.is_super_admin and self.complex.owner != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["complex"] = self.complex
        return kwargs

    def form_valid(self, form):
        form.instance.complex = self.complex
        messages.success(self.request, "Producto creado.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("products:complex_list", kwargs={"slug": self.complex.slug})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["complex"] = self.complex
        ctx["page_title"] = "Nuevo producto"
        ctx["submit_label"] = "Crear producto"
        return ctx


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/form.html"

    def dispatch(self, request, *args, **kwargs):
        self.complex = get_object_or_404(Complex, slug=kwargs["slug"])
        if not request.user.is_super_admin and self.complex.owner != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["complex"] = self.complex
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Producto actualizado.")
        return reverse_lazy("products:complex_list", kwargs={"slug": self.complex.slug})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["complex"] = self.complex
        ctx["page_title"] = f"Editar — {self.object.name}"
        ctx["submit_label"] = "Guardar cambios"
        return ctx


class StockAdjustmentView(LoginRequiredMixin, View):
    def post(self, request, slug, pk):
        complex = get_object_or_404(Complex, slug=slug)
        if not request.user.is_super_admin and complex.owner != request.user:
            raise PermissionDenied

        product = get_object_or_404(Product, pk=pk, complex=complex)
        form = StockAdjustmentForm(request.POST)

        if form.is_valid():
            qty = form.cleaned_data["quantity"]
            new_stock = product.stock + qty
            if new_stock < 0:
                messages.error(request, "Stock insuficiente.")
                return redirect("products:complex_list", slug=slug)

            product.stock = new_stock
            product.save(update_fields=["stock"])

            StockMovement.objects.create(
                product=product,
                movement_type=StockMovementType.IN if qty > 0 else StockMovementType.OUT,
                quantity=qty,
                stock_after=new_stock,
                notes=form.cleaned_data["notes"],
                created_by=request.user,
            )
            messages.success(request, f"Stock actualizado. Nuevo stock: {new_stock}.")

        return redirect("products:complex_list", slug=slug)


class QuickSaleView(LoginRequiredMixin, View):
    """Venta rápida desde mostrador."""

    def get(self, request, slug):
        complex = get_object_or_404(Complex, slug=slug)
        if not request.user.is_super_admin and complex.owner != request.user:
            raise PermissionDenied
        form = SaleItemForm(complex=complex)
        sales = Sale.objects.filter(complex=complex).prefetch_related("items__product").order_by("-created_at")[:10]
        return self._render(request, complex, form, sales)

    def post(self, request, slug):
        complex = get_object_or_404(Complex, slug=slug)
        if not request.user.is_super_admin and complex.owner != request.user:
            raise PermissionDenied

        form = SaleItemForm(request.POST, complex=complex)
        if form.is_valid():
            product = form.cleaned_data["product"]
            quantity = form.cleaned_data["quantity"]

            if product.stock < quantity:
                messages.error(request, f"Stock insuficiente. Disponible: {product.stock}.")
                return redirect("products:quick_sale", slug=slug)

            # Crear venta
            sale = Sale.objects.create(complex=complex, sold_by=request.user)
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=product.price,
            )
            sale.recalculate_total()

            # Descontar stock
            product.stock -= quantity
            product.save(update_fields=["stock"])

            StockMovement.objects.create(
                product=product,
                movement_type=StockMovementType.OUT,
                quantity=-quantity,
                stock_after=product.stock,
                notes=f"Venta #{sale.id}",
                created_by=request.user,
            )

            messages.success(request, f"Venta registrada. Total: ${sale.total}.")
            return redirect("products:quick_sale", slug=slug)

        sales = Sale.objects.filter(complex=complex).prefetch_related("items__product").order_by("-created_at")[:10]
        return self._render(request, complex, form, sales)

    def _render(self, request, complex, form, sales):
        from django.shortcuts import render
        return render(request, "products/quick_sale.html", {
            "complex": complex,
            "form": form,
            "sales": sales,
            "page_title": f"Venta rápida — {complex.name}",
        })