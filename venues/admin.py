from django.contrib import admin
from .models import Venue, Classroom, Lab, SeminarHall

admin.site.register(Venue)
admin.site.register(Classroom)
admin.site.register(Lab)
admin.site.register(SeminarHall)