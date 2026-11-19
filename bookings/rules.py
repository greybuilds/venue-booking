"""Booking rules. One class per rule, all the same shape:

    rule.validate(booking)  ->  returns nothing, or raises BookingError("clear reason")

To add a rule: write one class and add it to RULES. Nothing else changes.
"""
from abc import ABC, abstractmethod
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.utils import timezone

from .exceptions import BookingError


def local(dt):
    """Convert an aware datetime to the project time zone (Asia/Karachi)."""
    return timezone.localtime(dt)


def fmt(dt):
    return local(dt).strftime("%a %d %b, %I:%M %p")


def overlaps(s1, e1, s2, e2):
    """Strict on purpose: back to back (one ends 2pm, next starts 2pm) is fine."""
    return s1 < e2 and e1 > s2


def week_bounds(dt):
    """Monday 00:00 to next Monday 00:00 (local time) for the week containing dt.

    The one place the week is defined. Reused by WeeklyQuota.
    """
    d = local(dt)
    monday = d.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=d.weekday())
    return monday, monday + timedelta(days=7)


class BookingRule(ABC):
    @abstractmethod
    def validate(self, booking):
        """Return nothing if the booking is fine, else raise BookingError."""


class NoClash(BookingRule):
    def validate(self, booking):
        clash = booking.venue.conflicting_bookings(
            booking.start, booking.end, exclude_pk=booking.pk
        ).first()
        if clash:
            raise BookingError(
                f"{booking.venue} is already booked {fmt(clash.start)} to "
                f"{local(clash.end).strftime('%I:%M %p')}."
            )


class OpeningHours(BookingRule):
    def validate(self, booking):
        venue = booking.venue
        start, end = local(booking.start), local(booking.end)
        if start.date() != end.date():
            raise BookingError(f"{venue} closes at {venue.closes_at:%I:%M %p}; a booking cannot run past midnight.")
        if start.time() < venue.opens_at:
            raise BookingError(f"{venue} opens at {venue.opens_at:%I:%M %p}.")
        if end.time() > venue.closes_at:
            raise BookingError(f"{venue} closes at {venue.closes_at:%I:%M %p}.")


class MaxDuration(BookingRule):
    def validate(self, booking):
        limit = timedelta(hours=booking.venue.max_hours)
        if booking.duration > limit:
            raise BookingError(f"{booking.venue} allows at most {booking.venue.max_hours} hours per booking.")


class WeeklyQuota(BookingRule):
    """A society may book only so many hours per Monday to Sunday week.

    The limit is settings.SOCIETY_WEEKLY_QUOTA_HOURS (default 10). A booking
    counts towards the week it starts in.
    """

    def validate(self, booking):
        limit = timedelta(hours=getattr(settings, "SOCIETY_WEEKLY_QUOTA_HOURS", 10))
        week_start, week_end = week_bounds(booking.start)
        others = booking.society.bookings.filter(
            status__in=booking.BLOCKING, start__gte=week_start, start__lt=week_end
        ).exclude(pk=booking.pk)
        used = sum((b.duration for b in others), timedelta())
        if used + booking.duration > limit:
            hours_left = max(limit - used, timedelta()).total_seconds() / 3600
            raise BookingError(
                f"{booking.society} has only {hours_left:g} hours left this week "
                f"(limit {limit.total_seconds() / 3600:g})."
            )


class BlackoutDate(BookingRule):
    """No bookings during exam weeks, holidays, maintenance or timetabled classes.

    The blocked ranges belong to Member 3 (blocked dates + timetable import).
    Contract: a model venues.BlockedDate with fields
        venue (nullable ForeignKey: null = the whole campus), start, end (datetimes), reason.
    Until that model exists this rule passes everything.
    """

    def validate(self, booking):
        try:
            Blocked = apps.get_model("venues", "BlockedDate")
        except LookupError:
            return
        hit = (
            Blocked.objects.filter(start__lt=booking.end, end__gt=booking.start)
            .filter(venue__isnull=True)
            .first()
            or Blocked.objects.filter(
                venue=booking.venue, start__lt=booking.end, end__gt=booking.start
            ).first()
        )
        if hit:
            raise BookingError(f"Not available: {getattr(hit, 'reason', '') or 'blocked date'}.")


# Cheap checks first, NoClash last (it queries the database).
RULES = [OpeningHours(), MaxDuration(), BlackoutDate(), WeeklyQuota(), NoClash()]
