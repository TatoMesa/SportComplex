from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.models import UserRole
from .forms import ComplexForm, CourtForm
from .models import Complex, Court


class ComplexListView(LoginRequiredMixin, ListView):
    model = Complex
    template_name = "complexes/list.html"
    context_object_name = "complexes"
    paginate_by = 12

    def get_queryset(self):
        qs = Complex.objects.select_related("owner")
        # Super admin ve todos — admin de complejo solo los suyos
        if not self.request.user.is_super_admin:
            qs = qs.filter(owner=self.request.user)
        return qs


class ComplexCreateView(LoginRequiredMixin, CreateView):
    model = Complex
    form_class = ComplexForm
    template_name = "complexes/form.html"
    success_url = reverse_lazy("complexes:list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in (UserRole.SUPER_ADMIN, UserRole.COMPLEX_ADMIN):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Complejo creado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Nuevo complejo"
        ctx["submit_label"] = "Crear complejo"
        return ctx


class ComplexUpdateView(LoginRequiredMixin, UpdateView):
    model = Complex
    form_class = ComplexForm
    template_name = "complexes/form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.is_super_admin and obj.owner != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Complejo actualizado correctamente.")
        return reverse_lazy("complexes:detail", kwargs={"slug": self.object.slug})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Editar — {self.object.name}"
        ctx["submit_label"] = "Guardar cambios"
        return ctx


class ComplexDetailView(LoginRequiredMixin, DetailView):
    model = Complex
    template_name = "complexes/detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.is_super_admin and obj.owner != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["courts"] = self.object.courts.select_related("sport").order_by("sport__name", "name")
        return ctx


class CourtCreateView(LoginRequiredMixin, CreateView):
    model = Court
    form_class = CourtForm
    template_name = "complexes/court_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.complex = get_object_or_404(Complex, slug=kwargs["slug"])
        if not request.user.is_super_admin and self.complex.owner != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        # Admin de complejo activa directo, superadmin deja en PENDING para revisión
        if self.request.user.is_complex_admin:
            form.instance.status = "ACTIVE"
        messages.success(self.request, "Complejo creado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("complexes:detail", kwargs={"slug": self.complex.slug})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["complex"] = self.complex
        ctx["page_title"] = f"Nueva cancha — {self.complex.name}"
        ctx["submit_label"] = "Agregar cancha"
        return ctx