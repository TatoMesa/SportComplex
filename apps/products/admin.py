from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Product, ProductCategory, Sale, SaleItem, StockMovement


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "complex")
    list_filter = ("complex",)
    search_fields = ("name",)


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ("stock_after", "created_at", "created_by")
    fields = ("movement_type", "quantity", "stock_after", "notes", "created_by", "created_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "complex", "category", "price", "stock", "min_stock", "is_low_stock", "is_active")
    list_filter = ("complex", "category", "is_active")
    search_fields = ("name",)
    inlines = [StockMovementInline]

    @admin.display(boolean=True, description="Stock bajo")
    def is_low_stock(self, obj):
        return obj.is_low_stock


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ("product", "quantity", "unit_price", "subtotal")
    readonly_fields = ("subtotal",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "complex", "total", "sold_by", "created_at")
    list_filter = ("complex",)
    inlines = [SaleItemInline]
    readonly_fields = ("total", "created_at")