import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]