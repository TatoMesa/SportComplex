import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", _("Super Administrador")
    COMPLEX_ADMIN = "COMPLEX_ADMIN", _("Administrador de Complejo")
    END_USER = "END_USER", _("Usuario")


class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(_("email"), unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.END_USER,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_complex_admin(self) -> bool:
        return self.role == UserRole.COMPLEX_ADMIN

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def __str__(self) -> str:
        return self.email


class Profile(BaseModel):
    """
    Datos extendidos del usuario.
    Separado de User para no tocar AbstractUser más de lo necesario.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("usuario"),
    )
    phone = models.CharField(_("teléfono"), max_length=20, blank=True)
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/",
        null=True,
        blank=True,
    )
    bio = models.TextField(_("bio"), max_length=300, blank=True)
    birth_date = models.DateField(_("fecha de nacimiento"), null=True, blank=True)

    class Meta:
        verbose_name = _("perfil")
        verbose_name_plural = _("perfiles")

    def __str__(self) -> str:
        return f"Perfil de {self.user.email}"

    @property
    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar.url
        return "/static/img/default-avatar.svg"