from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from apps.complexes.models import Complex, Court
from apps.reservations.models import Reservation, ReservationStatus


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()

        if user.is_super_admin:
            ctx.update(self._super_admin_context(today))
        elif user.is_complex_admin:
            ctx.update(self._complex_admin_context(user, today))
        else:
            ctx.update(self._end_user_context(user, today))

        ctx["today"] = today
        return ctx

    def _super_admin_context(self, today: object) -> dict:
        reservations = Reservation.objects.all()
        return {
            "stats": [
                {
                    "label": "Complejos activos",
                    "value": Complex.objects.filter(status="ACTIVE").count(),
                    "color": "blue",
                },
                {
                    "label": "Reservas hoy",
                    "value": reservations.filter(date=today).count(),
                    "color": "green",
                },
                {
                    "label": "Reservas este mes",
                    "value": reservations.filter(
                        date__month=today.month,
                        date__year=today.year,
                    ).count(),
                    "color": "purple",
                },
                {
                    "label": "Ingresos este mes",
                    "value": reservations.filter(
                        date__month=today.month,
                        date__year=today.year,
                        status=ReservationStatus.CONFIRMED,
                    ).aggregate(total=Sum("total_amount"))["total"] or 0,
                    "color": "amber",
                    "prefix": "$",
                },
            ],
            "recent_reservations": Reservation.objects.select_related(
                "court__complex", "court__sport", "user"
            ).order_by("-created_at")[:8],
            "role": "super_admin",
        }

    def _complex_admin_context(self, user, today: object) -> dict:
        from django.db.models import Q
        my_complexes = Complex.objects.filter(owner=user)
        reservations = Reservation.objects.filter(court__complex__in=my_complexes)

        return {
            "stats": [
                {
                    "label": "Mis complejos",
                    "value": my_complexes.count(),
                    "color": "blue",
                },
                {
                    "label": "Reservas hoy",
                    "value": reservations.filter(date=today).count(),
                    "color": "green",
                },
                {
                    "label": "Confirmadas este mes",
                    "value": reservations.filter(
                        date__month=today.month,
                        date__year=today.year,
                        status=ReservationStatus.CONFIRMED,
                    ).count(),
                    "color": "purple",
                },
                {
                    "label": "Ingresos este mes",
                    "value": reservations.filter(
                        date__month=today.month,
                        date__year=today.year,
                        status=ReservationStatus.CONFIRMED,
                    ).aggregate(total=Sum("total_amount"))["total"] or 0,
                    "color": "amber",
                    "prefix": "$",
                },
            ],
            "recent_reservations": reservations.select_related(
                "court__complex", "court__sport", "user"
            ).order_by("-created_at")[:8],
            "my_complexes": my_complexes.annotate(
                total_courts=Count("courts"),
                reservations_today=Count(
                    "courts__reservations",
                    filter=Q(courts__reservations__date=today),
                ),
            ),
            "role": "complex_admin",
        }

    def _end_user_context(self, user, today: object) -> dict:
        my_reservations = Reservation.objects.filter(user=user)
        return {
            "stats": [
                {
                    "label": "Mis reservas",
                    "value": my_reservations.count(),
                    "color": "blue",
                },
                {
                    "label": "Próximas",
                    "value": my_reservations.filter(
                        date__gte=today,
                        status__in=[
                            ReservationStatus.PENDING,
                            ReservationStatus.CONFIRMED,
                        ],
                    ).count(),
                    "color": "green",
                },
                {
                    "label": "Completadas",
                    "value": my_reservations.filter(
                        status=ReservationStatus.COMPLETED
                    ).count(),
                    "color": "purple",
                },
                {
                    "label": "Canceladas",
                    "value": my_reservations.filter(
                        status=ReservationStatus.CANCELLED
                    ).count(),
                    "color": "amber",
                },
            ],
            "recent_reservations": my_reservations.select_related(
                "court__complex", "court__sport"
            ).order_by("-created_at")[:8],
            "role": "end_user",
        }