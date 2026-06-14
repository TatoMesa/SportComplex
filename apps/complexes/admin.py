from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Complex, ComplexSport, Court, Schedule, Sport


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


class ComplexSportInline(admin.TabularInline):
    model = ComplexSport
    extra = 1


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 7
    max_num = 7


class CourtInline(admin.TabularInline):
    model = Court
    extra = 0
    fields = ("name", "sport", "surface", "price_per_hour", "is_indoor", "is_active")


@admin.register(Complex)
class ComplexAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "city", "status", "created_at")
    list_filter = ("status", "city")
    search_fields = ("name", "city", "owner__email")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ComplexSportInline, ScheduleInline, CourtInline]
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("owner", "name", "slug", "status")}),
        (_("Información"), {"fields": ("description", "address", "city", "province", "phone", "email")}),
        (_("Imágenes"), {"fields": ("logo", "cover")}),
        (_("Fechas"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ("name", "complex", "sport", "surface", "price_per_hour", "is_active")
    list_filter = ("sport", "surface", "is_active", "is_indoor")
    search_fields = ("name", "complex__name")