from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from apps.accounts.models import User


class Sport(BaseModel):
    """Deporte: pádel, fútbol 5, tenis, hockey, etc."""

    name = models.CharField(_("nombre"), max_length=60, unique=True)
    icon = models.CharField(_("ícono"), max_length=60, blank=True, help_text="Clase CSS o nombre de ícono")
    is_active = models.BooleanField(_("activo"), default=True)

    class Meta:
        verbose_name = _("deporte")
        verbose_name_plural = _("deportes")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ComplexStatus(models.TextChoices):
    PENDING = "PENDING", _("Pendiente")
    ACTIVE = "ACTIVE", _("Activo")
    SUSPENDED = "SUSPENDED", _("Suspendido")


class Complex(BaseModel):
    """Complejo deportivo. Cada uno tiene su propio admin."""

    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="owned_complexes",
        verbose_name=_("propietario"),
    )
    name = models.CharField(_("nombre"), max_length=120)
    slug = models.SlugField(_("slug"), unique=True, max_length=130)
    description = models.TextField(_("descripción"), blank=True)
    address = models.CharField(_("dirección"), max_length=255)
    city = models.CharField(_("ciudad"), max_length=100)
    province = models.CharField(_("provincia"), max_length=100, blank=True)
    phone = models.CharField(_("teléfono"), max_length=20, blank=True)
    email = models.EmailField(_("email"), blank=True)
    logo = models.ImageField(_("logo"), upload_to="complexes/logos/", null=True, blank=True)
    cover = models.ImageField(_("portada"), upload_to="complexes/covers/", null=True, blank=True)
    status = models.CharField(
        _("estado"),
        max_length=12,
        choices=ComplexStatus.choices,
        default=ComplexStatus.PENDING,
    )
    sports = models.ManyToManyField(
        Sport,
        through="ComplexSport",
        related_name="complexes",
        verbose_name=_("deportes"),
    )

    class Meta:
        verbose_name = _("complejo")
        verbose_name_plural = _("complejos")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["city"]),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    @property
    def is_active(self) -> bool:
        return self.status == ComplexStatus.ACTIVE

    @property
    def logo_url(self) -> str:
        if self.logo:
            return self.logo.url
        return "/static/img/default-complex.svg"


class ComplexSport(BaseModel):
    """Relación entre complejo y deportes que ofrece."""

    complex = models.ForeignKey(Complex, on_delete=models.CASCADE)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("deporte del complejo")
        verbose_name_plural = _("deportes del complejo")
        unique_together = [("complex", "sport")]


class CourtSurface(models.TextChoices):
    CLAY = "CLAY", _("Tierra")
    GRASS = "GRASS", _("Césped")
    SYNTHETIC = "SYNTHETIC", _("Sintético")
    HARD = "HARD", _("Duro")
    WOOD = "WOOD", _("Madera")
    CONCRETE = "CONCRETE", _("Cemento")


class Court(BaseModel):
    """Cancha dentro de un complejo."""

    complex = models.ForeignKey(
        Complex,
        on_delete=models.CASCADE,
        related_name="courts",
        verbose_name=_("complejo"),
    )
    sport = models.ForeignKey(
        Sport,
        on_delete=models.PROTECT,
        related_name="courts",
        verbose_name=_("deporte"),
    )
    name = models.CharField(_("nombre"), max_length=80)
    surface = models.CharField(
        _("superficie"),
        max_length=12,
        choices=CourtSurface.choices,
        blank=True,
    )
    price_per_hour = models.DecimalField(
        _("precio por hora"),
        max_digits=10,
        decimal_places=2,
    )
    is_indoor = models.BooleanField(_("cubierta"), default=False)
    is_active = models.BooleanField(_("activa"), default=True)
    notes = models.TextField(_("notas"), blank=True)

    class Meta:
        verbose_name = _("cancha")
        verbose_name_plural = _("canchas")
        ordering = ["complex", "sport", "name"]
        indexes = [
            models.Index(fields=["complex", "is_active"]),
            models.Index(fields=["sport"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} — {self.complex.name}"


class Schedule(BaseModel):
    """
    Horario de apertura/cierre por día de la semana para cada complejo.
    """

    WEEKDAYS = [
        (0, _("Lunes")),
        (1, _("Martes")),
        (2, _("Miércoles")),
        (3, _("Jueves")),
        (4, _("Viernes")),
        (5, _("Sábado")),
        (6, _("Domingo")),
    ]

    complex = models.ForeignKey(
        Complex,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name=_("complejo"),
    )
    weekday = models.PositiveSmallIntegerField(_("día"), choices=WEEKDAYS)
    open_time = models.TimeField(_("apertura"))
    close_time = models.TimeField(_("cierre"))
    is_closed = models.BooleanField(_("cerrado"), default=False)

    class Meta:
        verbose_name = _("horario")
        verbose_name_plural = _("horarios")
        ordering = ["weekday"]
        unique_together = [("complex", "weekday")]

    def __str__(self) -> str:
        return f"{self.complex.name} — {self.get_weekday_display()}"
    