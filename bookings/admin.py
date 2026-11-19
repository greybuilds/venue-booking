from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Status is changed only through Booking methods / BookingService, never by editing the field.
    list_display = ("society", "venue", "start", "end", "status", "booked_by")
    list_filter = ("status", "venue")
    readonly_fields = ("status", "created_at")
