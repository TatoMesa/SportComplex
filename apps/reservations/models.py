from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from apps.accounts.models import User
from apps.complexes.models import Court


class ReservationStatus(models.TextChoices):
    PENDING = "PENDING", _("Pendiente")
    CONFIRMED = "CONFIRMED", _("Confirmada")
    CANCELLED = "CANCELLED", _("Cancelada")
    COMPLETED = "COMPLETED", _("Completada")
    NO_SHOW = "NO_SHOW", _("No se presentó")


class Reservation(BaseModel):
    """
    Reserva de una cancha.
    La constraint no_double_booking evita solapamiento a nivel de base de datos.
    """

    court = models.ForeignKey(
        Court,
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name=_("cancha"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name=_("usuario"),
    )
    date = models.DateField(_("fecha"))
    start_time = models.TimeField(_("inicio"))
    end_time = models.TimeField(_("fin"))
    status = models.CharField(
        _("estado"),
        max_length=12,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
    )
    total_amount = models.DecimalField(
        _("total"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    notes = models.TextField(_("notas"), blank=True)
    cancelled_at = models.DateTimeField(_("cancelada el"), null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_reservations",
        verbose_name=_("cancelada por"),
    )

    class Meta:
        verbose_name = _("reserva")
        verbose_name_plural = _("reservas")
        ordering = ["-date", "-start_time"]
        indexes = [
            models.Index(fields=["date", "status"]),
            models.Index(fields=["court", "date"]),
            models.Index(fields=["user"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["court", "date", "start_time"],
                condition=models.Q(status__in=["PENDING", "CONFIRMED"]),
                name="no_double_booking",
            )
        ]

    def clean(self) -> None:
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(
                    _("La hora de inicio debe ser anterior a la hora de fin.")
                )

        # Verificar solapamiento con otras reservas activas
        if self.court_id and self.date and self.start_time and self.end_time:
            overlapping = Reservation.objects.filter(
                court=self.court_id,
                date=self.date,
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError(
                    _("Ya existe una reserva en ese horario para esta cancha.")
                )

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.court} — {self.date} {self.start_time}"

    @property
    def duration_hours(self) -> float:
        start = self.start_time.hour + self.start_time.minute / 60
        end = self.end_time.hour + self.end_time.minute / 60
        return end - start

    @property
    def is_cancellable(self) -> bool:
        return self.status in (ReservationStatus.PENDING, ReservationStatus.CONFIRMED)


class PaymentMethod(models.TextChoices):
    CASH = "CASH", _("Efectivo")
    TRANSFER = "TRANSFER", _("Transferencia")
    CARD = "CARD", _("Tarjeta")
    MP = "MP", _("Mercado Pago")


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", _("Pendiente")
    PAID = "PAID", _("Pagado")
    REFUNDED = "REFUNDED", _("Reembolsado")


class Payment(BaseModel):
    """Pago asociado a una reserva."""

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name="payment",
        verbose_name=_("reserva"),
    )
    amount = models.DecimalField(_("monto"), max_digits=10, decimal_places=2)
    method = models.CharField(
        _("método"),
        max_length=12,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    status = models.CharField(
        _("estado"),
        max_length=12,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    paid_at = models.DateTimeField(_("pagado el"), null=True, blank=True)
    notes = models.TextField(_("notas"), blank=True)

    class Meta:
        verbose_name = _("pago")
        verbose_name_plural = _("pagos")

    def __str__(self) -> str:
        return f"Pago {self.reservation} — {self.get_status_display()}"


class WaitingList(BaseModel):
    """
    Usuario interesado en una cancha/fecha/horario.
    Se notifica automáticamente si se libera un turno.
    """

    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name="waiting_list",
        verbose_name=_("cancha"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="waiting_list",
        verbose_name=_("usuario"),
    )
    date = models.DateField(_("fecha"))
    start_time = models.TimeField(_("inicio deseado"))
    end_time = models.TimeField(_("fin deseado"))
    notified = models.BooleanField(_("notificado"), default=False)
    notified_at = models.DateTimeField(_("notificado el"), null=True, blank=True)

    class Meta:
        verbose_name = _("lista de espera")
        verbose_name_plural = _("lista de espera")
        ordering = ["date", "start_time", "created_at"]
        indexes = [
            models.Index(fields=["court", "date", "notified"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} esperando {self.court} el {self.date}"