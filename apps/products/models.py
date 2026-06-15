from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from apps.accounts.models import User
from apps.complexes.models import Complex
from apps.reservations.models import Reservation


class ProductCategory(BaseModel):
    """Categoría de producto: Paletas, Pelotas, Bebidas, etc."""

    complex = models.ForeignKey(
        Complex,
        on_delete=models.CASCADE,
        related_name="product_categories",
        verbose_name=_("complejo"),
    )
    name = models.CharField(_("nombre"), max_length=80)
    description = models.TextField(_("descripción"), blank=True)

    class Meta:
        verbose_name = _("categoría")
        verbose_name_plural = _("categorías")
        ordering = ["name"]
        unique_together = [("complex", "name")]

    def __str__(self) -> str:
        return f"{self.name} — {self.complex.name}"


class Product(BaseModel):
    """Producto del inventario de un complejo."""

    complex = models.ForeignKey(
        Complex,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name=_("complejo"),
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name=_("categoría"),
    )
    name = models.CharField(_("nombre"), max_length=120)
    description = models.TextField(_("descripción"), blank=True)
    price = models.DecimalField(_("precio"), max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(_("stock"), default=0)
    min_stock = models.PositiveIntegerField(_("stock mínimo"), default=5)
    is_active = models.BooleanField(_("activo"), default=True)

    class Meta:
        verbose_name = _("producto")
        verbose_name_plural = _("productos")
        ordering = ["category", "name"]
        indexes = [
            models.Index(fields=["complex", "is_active"]),
            models.Index(fields=["stock"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} — {self.complex.name}"

    @property
    def is_low_stock(self) -> bool:
        return self.stock <= self.min_stock

    @property
    def is_out_of_stock(self) -> bool:
        return self.stock == 0


class StockMovementType(models.TextChoices):
    IN = "IN", _("Entrada")
    OUT = "OUT", _("Salida")
    ADJUSTMENT = "ADJUSTMENT", _("Ajuste")


class StockMovement(BaseModel):
    """Registro de cada movimiento de stock."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="movements",
        verbose_name=_("producto"),
    )
    movement_type = models.CharField(
        _("tipo"),
        max_length=12,
        choices=StockMovementType.choices,
    )
    quantity = models.IntegerField(_("cantidad"))
    stock_after = models.PositiveIntegerField(_("stock resultante"))
    notes = models.TextField(_("notas"), blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="stock_movements",
        verbose_name=_("registrado por"),
    )

    class Meta:
        verbose_name = _("movimiento de stock")
        verbose_name_plural = _("movimientos de stock")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_movement_type_display()} {self.quantity} — {self.product.name}"


class Sale(BaseModel):
    """Venta de productos. Puede estar asociada a una reserva."""

    complex = models.ForeignKey(
        Complex,
        on_delete=models.CASCADE,
        related_name="sales",
        verbose_name=_("complejo"),
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
        verbose_name=_("reserva"),
    )
    sold_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sales",
        verbose_name=_("vendido por"),
    )
    total = models.DecimalField(_("total"), max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(_("notas"), blank=True)

    class Meta:
        verbose_name = _("venta")
        verbose_name_plural = _("ventas")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["complex", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Venta {self.id} — {self.complex.name}"

    def recalculate_total(self) -> None:
        from django.db.models import Sum
        total = self.items.aggregate(t=Sum("subtotal"))["t"] or 0
        self.total = total
        self.save(update_fields=["total"])


class SaleItem(BaseModel):
    """Ítem de una venta."""

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("venta"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="sale_items",
        verbose_name=_("producto"),
    )
    quantity = models.PositiveIntegerField(_("cantidad"), default=1)
    unit_price = models.DecimalField(_("precio unitario"), max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(_("subtotal"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("ítem de venta")
        verbose_name_plural = _("ítems de venta")

    def save(self, *args, **kwargs) -> None:
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product.name}"