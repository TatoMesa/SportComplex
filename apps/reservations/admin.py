from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Payment, Reservation, WaitingList


class PaymentInline(admin.StackedInline):
    model = Payment
    can_delete = False
    extra = 0
    fields = ("amount", "method", "status", "paid_at", "notes")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("court", "user", "date", "start_time", "end_time", "status", "total_amount")
    list_filter = ("status", "date", "court__complex")
    search_fields = ("user__email", "court__name", "court__complex__name")
    ordering = ("-date", "-start_time")
    inlines = [PaymentInline]
    readonly_fields = ("created_at", "updated_at", "cancelled_at")

    fieldsets = (
        (None, {"fields": ("court", "user", "date", "start_time", "end_time")}),
        (_("Estado"), {"fields": ("status", "total_amount", "notes")}),
        (_("Cancelación"), {"fields": ("cancelled_at", "cancelled_by")}),
        (_("Fechas"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(WaitingList)
class WaitingListAdmin(admin.ModelAdmin):
    list_display = ("user", "court", "date", "start_time", "notified")
    list_filter = ("notified", "date")
    search_fields = ("user__email", "court__name")