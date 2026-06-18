from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView, ListView
from django.urls import reverse_lazy
from django.db.models import Count, Sum

from apps.reservations.models import Reservation, ReservationStatus
from .forms import ProfileUpdateForm, UserUpdateForm
from .models import Profile


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        reservations = Reservation.objects.filter(user=user)

        ctx["stats"] = {
            "total": reservations.count(),
            "confirmed": reservations.filter(status=ReservationStatus.CONFIRMED).count(),
            "completed": reservations.filter(status=ReservationStatus.COMPLETED).count(),
            "cancelled": reservations.filter(status=ReservationStatus.CANCELLED).count(),
            "total_spent": reservations.filter(
                status__in=[ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED]
            ).aggregate(t=Sum("total_amount"))["t"] or 0,
        }

        ctx["recent_reservations"] = reservations.select_related(
            "court__complex", "court__sport"
        ).order_by("-date")[:5]

        ctx["favorite_complexes"] = user.favorite_complexes.select_related(
            "complex"
        ).order_by("order")

        return ctx


class ProfileUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile_edit.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        ctx["user_form"] = UserUpdateForm(instance=user)
        ctx["profile_form"] = ProfileUpdateForm(instance=profile)
        return ctx

    def post(self, request, *args, **kwargs):
        from django.shortcuts import redirect
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("accounts:profile")

        ctx = self.get_context_data()
        ctx["user_form"] = user_form
        ctx["profile_form"] = profile_form
        return self.render_to_response(ctx)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        if "user_form" not in kwargs:
            ctx["user_form"] = UserUpdateForm(instance=user)
        if "profile_form" not in kwargs:
            ctx["profile_form"] = ProfileUpdateForm(instance=profile)
        return ctx


class MyReservationsView(LoginRequiredMixin, ListView):
    template_name = "accounts/my_reservations.html"
    context_object_name = "reservations"
    paginate_by = 15

    def get_queryset(self):
        qs = Reservation.objects.filter(
            user=self.request.user
        ).select_related("court__complex", "court__sport").order_by("-date")

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = ReservationStatus.choices
        ctx["selected_status"] = self.request.GET.get("status", "")
        return ctx