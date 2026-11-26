from datetime import timedelta

from django.conf import settings
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

    def approval_needed(self):
        """Does a booking here wait for an admin (PENDING) or confirm at once?"""
        return self.requires_approval

    def conflicting_bookings(self, start, end, exclude_pk=None):
        """Bookings that block [start, end) here, buffer minutes included.

        Only PENDING and CONFIRMED bookings block a slot. The overlap rule is
        strict (s1 < e2 and e1 > s2), so back to back bookings are allowed
        when the buffer is 0.
        """
        buffer = timedelta(minutes=self.buffer_minutes)
        qs = self.bookings.filter(
            status__in=("PENDING", "CONFIRMED"),
            start__lt=end + buffer,
            end__gt=start - buffer,
        )
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs

    def is_free(self, start, end, exclude_pk=None):
        return not self.conflicting_bookings(start, end, exclude_pk).exists()


class Classroom(Venue):
    has_projector = models.BooleanField(default=False)


class Lab(Venue):
    equipment = models.TextField(blank=True)
    supervisor = models.CharField(max_length=100, blank=True)


class SeminarHall(Venue):
    av_kit = models.TextField(blank=True)

class BlockedDate(models.Model):
    venue = models.ForeignKey(
        Venue,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    start = models.DateTimeField()
    end = models.DateTimeField()
    reason = models.CharField(max_length=120)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    def __str__(self):
        return self.reason