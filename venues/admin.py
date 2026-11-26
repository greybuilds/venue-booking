from django.contrib import admin
from .models import Venue, Classroom, Lab, SeminarHall, BlockedDate

admin.site.register(Venue)
admin.site.register(Classroom)
admin.site.register(Lab)
admin.site.register(SeminarHall)
@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ("reason", "venue", "start", "end", "created_by")
    exclude = ("created_by",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)