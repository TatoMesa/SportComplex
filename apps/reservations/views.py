from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.accounts.models import UserRole
from apps.complexes.models import Complex
from .forms import PaymentForm, ReservationForm
from .models import Payment, PaymentMethod, PaymentStatus, Reservation, ReservationStatus
import decimal

class ReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "reservations/list.html"
    context_object_name = "reservations"
    paginate_by = 20

    def get_queryset(self):
        qs = Reservation.objects.select_related(
            "court__complex", "court__sport", "user"
        )
        user = self.request.user

        if user.is_super_admin:
            pass  # ve todas
        elif user.is_complex_admin:
            # ve las de sus complejos
            qs = qs.filter(court__complex__owner=user)
        else:
            # usuario final ve solo las suyas
            qs = qs.filter(user=user)

        # Filtro por estado
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        # Filtro por fecha
        date = self.request.GET.get("date")
        if date:
            qs = qs.filter(date=date)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = ReservationStatus.choices
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["today"] = timezone.localdate()
        return ctx


class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "reservations/form.html"

    def dispatch(self, request, *args, **kwargs):
        # Si viene con slug de complejo, filtramos canchas de ese complejo
        slug = kwargs.get("slug")
        if slug:
            self.complex = get_object_or_404(Complex, slug=slug)
        else:
            self.complex = None
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["complex"] = self.complex
        return kwargs

    def form_valid(self, form):
        import decimal
        form.instance.user = self.request.user
        court = form.cleaned_data["court"]
        start = form.cleaned_data["start_time"]
        end = form.cleaned_data["end_time"]
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        hours = decimal.Decimal(end_minutes - start_minutes) / decimal.Decimal(60)
        total = (court.price_per_hour * hours).quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
        )
        form.instance.total_amount = total
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Reserva creada correctamente.")
            return response
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("reservations:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Nueva reserva"
        ctx["submit_label"] = "Crear reserva"
        ctx["complex"] = self.complex
        return ctx


class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = "reservations/detail.html"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        user = request.user
        if not user.is_super_admin:
            is_owner = obj.user == user
            is_complex_admin = (
                user.is_complex_admin and obj.court.complex.owner == user
            )
            if not (is_owner or is_complex_admin):
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["payment_form"] = PaymentForm(
            initial={"amount": self.object.total_amount}
        )
        ctx["can_cancel"] = self.object.is_cancellable
        return ctx


class ReservationCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)
        user = request.user

        if not user.is_super_admin:
            is_owner = reservation.user == user
            is_complex_admin = (
                user.is_complex_admin and reservation.court.complex.owner == user
            )
            if not (is_owner or is_complex_admin):
                raise PermissionDenied

        if not reservation.is_cancellable:
            messages.error(request, "Esta reserva no se puede cancelar.")
            return redirect("reservations:detail", pk=pk)

        reservation.status = ReservationStatus.CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.cancelled_by = user
        reservation.save()
        messages.success(request, "Reserva cancelada.")
        return redirect("reservations:list")


class ConfirmPaymentView(LoginRequiredMixin, View):
    """El admin del complejo confirma el pago de una reserva."""

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)
        user = request.user

        if not user.is_super_admin:
            if not (user.is_complex_admin and reservation.court.complex.owner == user):
                raise PermissionDenied

        form = PaymentForm(request.POST)
        if form.is_valid():
            payment, created = Payment.objects.get_or_create(reservation=reservation)
            payment.amount = form.cleaned_data["amount"]
            payment.method = form.cleaned_data["method"]
            payment.status = PaymentStatus.PAID
            payment.notes = form.cleaned_data["notes"]
            from django.utils import timezone
            payment.paid_at = timezone.now()
            payment.save()

            reservation.status = ReservationStatus.CONFIRMED
            reservation.save()

            messages.success(request, "Pago confirmado. Reserva confirmada.")
        else:
            messages.error(request, "Error al confirmar el pago.")

        return redirect("reservations:detail", pk=pk)