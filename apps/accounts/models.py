import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


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

    def __str__(self) -> str:
        return self.email