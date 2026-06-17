from datetime import date, time, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View

from apps.accounts.models import FavoriteComplex
from apps.complexes.models import Complex, Sport
from services.search_service import get_active_cities, get_available_courts, get_sports_with_courts

HOUR_CHOICES = [(f"{h:02d}:00", f"{h:02d}:00") for h in range(6, 25)]


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "search/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sports"] = get_sports_with_courts()
        ctx["cities"] = get_active_cities()
        ctx["hour_choices"] = HOUR_CHOICES
        ctx["today"] = timezone.localdate().isoformat()
        ctx["tomorrow"] = (timezone.localdate() + timedelta(days=1)).isoformat()

        # Si hay parámetros de búsqueda, ejecutar
        params = self.request.GET
        if params.get("date") and params.get("start_time") and params.get("end_time"):
            try:
                search_date = date.fromisoformat(params["date"])
                start_h = int(params["start_time"].split(":")[0])
                end_h = int(params["end_time"].split(":")[0])
                start_time = time(start_h, 0)
                end_time = time(end_h, 0) if end_h < 24 else time(23, 59)

                if start_time >= end_time:
                    ctx["error"] = "La hora de inicio debe ser anterior a la hora de fin."
                else:
                    results = get_available_courts(
                        search_date=search_date,
                        start_time=start_time,
                        end_time=end_time,
                        sport_id=params.get("sport") or None,
                        city=params.get("city") or None,
                        max_price=params.get("max_price") or None,
                        complex_id=params.get("complex") or None,
                        user=self.request.user,
                    )
                    ctx["results"] = results
                    ctx["result_count"] = len(results)
                    ctx["searched"] = True
                    ctx["search_date"] = search_date
                    ctx["start_time"] = params["start_time"]
                    ctx["end_time"] = params["end_time"]

            except (ValueError, KeyError):
                ctx["error"] = "Parámetros de búsqueda inválidos."

        # Favoritos del usuario
        if self.request.user.is_authenticated:
            ctx["favorites"] = FavoriteComplex.objects.filter(
                user=self.request.user
            ).select_related("complex").order_by("order")

        return ctx


class ToggleFavoriteView(LoginRequiredMixin, View):
    """Agrega o quita un complejo de favoritos."""

    def post(self, request, slug):
        complex = get_object_or_404(Complex, slug=slug)
        fav, created = FavoriteComplex.objects.get_or_create(
            user=request.user,
            complex=complex,
        )
        if not created:
            fav.delete()
            messages.success(request, f"{complex.name} quitado de favoritos.")
        else:
            messages.success(request, f"{complex.name} agregado a favoritos.")

        next_url = request.POST.get("next", "search:index")
        return redirect(request.POST.get("next_url", "/buscar/"))