from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from apps.accounts.models import User
from apps.complexes.models import Complex, Sport


class TournamentFormat(models.TextChoices):
    SINGLE_ELIMINATION = "SINGLE_ELIM", _("Eliminación simple")
    DOUBLE_ELIMINATION = "DOUBLE_ELIM", _("Eliminación doble")
    ROUND_ROBIN = "ROUND_ROBIN", _("Round Robin")
    AMERICANO = "AMERICANO", _("Americano")
    MEXICANO = "MEXICANO", _("Mexicano")


class TournamentStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Borrador")
    OPEN = "OPEN", _("Inscripciones abiertas")
    IN_PROGRESS = "IN_PROGRESS", _("En curso")
    FINISHED = "FINISHED", _("Finalizado")
    CANCELLED = "CANCELLED", _("Cancelado")


class Tournament(BaseModel):
    complex = models.ForeignKey(
        Complex,
        on_delete=models.CASCADE,
        related_name="tournaments",
        verbose_name=_("complejo"),
    )
    sport = models.ForeignKey(
        Sport,
        on_delete=models.PROTECT,
        related_name="tournaments",
        verbose_name=_("deporte"),
    )
    name = models.CharField(_("nombre"), max_length=120)
    description = models.TextField(_("descripción"), blank=True)
    format = models.CharField(
        _("formato"),
        max_length=12,
        choices=TournamentFormat.choices,
        default=TournamentFormat.ROUND_ROBIN,
    )
    status = models.CharField(
        _("estado"),
        max_length=12,
        choices=TournamentStatus.choices,
        default=TournamentStatus.DRAFT,
    )
    start_date = models.DateField(_("fecha de inicio"))
    end_date = models.DateField(_("fecha de fin"), null=True, blank=True)
    max_teams = models.PositiveSmallIntegerField(_("máximo de equipos"), default=8)
    prize_info = models.TextField(_("premios"), blank=True)

    class Meta:
        verbose_name = _("torneo")
        verbose_name_plural = _("torneos")
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["complex", "status"]),
            models.Index(fields=["sport"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} — {self.complex.name}"

    @property
    def is_open(self) -> bool:
        return self.status == TournamentStatus.OPEN


class TournamentCategory(BaseModel):
    """
    Categoría dentro de un torneo.
    Ej: Primera, Segunda, Mixto, Sub-18.
    """

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name=_("torneo"),
    )
    name = models.CharField(_("nombre"), max_length=80)
    description = models.TextField(_("descripción"), blank=True)
    max_teams = models.PositiveSmallIntegerField(_("máximo de equipos"), default=8)

    class Meta:
        verbose_name = _("categoría")
        verbose_name_plural = _("categorías")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} — {self.tournament.name}"


class Team(BaseModel):
    """Equipo o pareja inscripta en una categoría."""

    category = models.ForeignKey(
        TournamentCategory,
        on_delete=models.CASCADE,
        related_name="teams",
        verbose_name=_("categoría"),
    )
    name = models.CharField(_("nombre"), max_length=80)
    players = models.ManyToManyField(
        User,
        related_name="tournament_teams",
        verbose_name=_("jugadores"),
        blank=True,
    )
    seed = models.PositiveSmallIntegerField(_("cabeza de serie"), default=0)

    class Meta:
        verbose_name = _("equipo")
        verbose_name_plural = _("equipos")
        ordering = ["seed", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.category.name})"


class MatchStatus(models.TextChoices):
    PENDING = "PENDING", _("Pendiente")
    IN_PROGRESS = "IN_PROGRESS", _("En curso")
    FINISHED = "FINISHED", _("Finalizado")
    WALKOVER = "WALKOVER", _("Walkover")


class Match(BaseModel):
    """Partido entre dos equipos dentro de una categoría."""

    category = models.ForeignKey(
        TournamentCategory,
        on_delete=models.CASCADE,
        related_name="matches",
        verbose_name=_("categoría"),
    )
    round_number = models.PositiveSmallIntegerField(_("ronda"), default=1)
    match_number = models.PositiveSmallIntegerField(_("número de partido"), default=1)
    team_a = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches_as_a",
        verbose_name=_("equipo A"),
    )
    team_b = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches_as_b",
        verbose_name=_("equipo B"),
    )
    score_a = models.PositiveSmallIntegerField(_("puntos A"), null=True, blank=True)
    score_b = models.PositiveSmallIntegerField(_("puntos B"), null=True, blank=True)
    winner = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches_won",
        verbose_name=_("ganador"),
    )
    status = models.CharField(
        _("estado"),
        max_length=12,
        choices=MatchStatus.choices,
        default=MatchStatus.PENDING,
    )
    scheduled_at = models.DateTimeField(_("programado para"), null=True, blank=True)
    notes = models.TextField(_("notas"), blank=True)

    class Meta:
        verbose_name = _("partido")
        verbose_name_plural = _("partidos")
        ordering = ["round_number", "match_number"]

    def __str__(self) -> str:
        a = self.team_a.name if self.team_a else "BYE"
        b = self.team_b.name if self.team_b else "BYE"
        return f"R{self.round_number} — {a} vs {b}"