from django.db import models


class Venue(models.Model):
    name = models.CharField(max_length=100)
    building = models.CharField(max_length=100)
    floor = models.IntegerField()
    capacity = models.PositiveIntegerField()
    opens_at = models.TimeField()
    closes_at = models.TimeField()
    requires_approval = models.BooleanField(default=False)
    max_hours = models.PositiveIntegerField(default=4)
    buffer_minutes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Classroom(Venue):
    has_projector = models.BooleanField(default=False)


class Lab(Venue):
    equipment = models.TextField(blank=True)
    supervisor = models.CharField(max_length=100, blank=True)


class SeminarHall(Venue):
    av_kit = models.TextField(blank=True)