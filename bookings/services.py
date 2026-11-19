from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.utils import timezone

from venues.models import Venue

from .exceptions import BookingError, RulesFailed
from .models import Booking
from .rules import RULES


def run_rules(booking, rules=RULES):
    """Run EVERY rule and return all the reasons, so the rep sees every problem at once."""
    errors = []
    for rule in rules:
        try:
            rule.validate(booking)
        except BookingError as e:
            errors.append(str(e))
    return errors


def suggest_slots(booking, hours=(1, -1, 2, -2, 3, -3), limit=3):
    """Nearby slots at the same venue (same length) that pass every rule."""
    found = []
    for h in hours:
        start = booking.start + timedelta(hours=h)
        candidate = Booking(
            society=booking.society, venue=booking.venue, booked_by=booking.booked_by,
            start=start, end=start + booking.duration,
        )
        if start > timezone.now() and not run_rules(candidate):
            found.append((candidate.start, candidate.end))
            if len(found) == limit:
                break
    return sorted(found)


def _is_admin(user):
    return getattr(user, "role", None) == "ADMIN" or getattr(user, "is_superuser", False)


class BookingService:
    """The one place bookings are made and changed. Views stay thin and call this."""

    @staticmethod
    def request(society, venue, start, end, user):
        if not society.can_book(user):
            raise PermissionDenied("Only the President or VP of a verified society can book.")
        if timezone.is_naive(start) or timezone.is_naive(end):
            raise BookingError("Start and end must be timezone aware.")
        if end <= start:
            raise BookingError("The end time must be after the start time.")
        if start < timezone.now():
            raise BookingError("You cannot book a time in the past.")

        try:
            with transaction.atomic():
                # Lock the venue row: everyone booking this venue queues up here.
                # (SQLite ignores row locks. Real locking needs PostgreSQL.)
                venue = Venue.objects.select_for_update().get(pk=venue.pk)
                booking = Booking(
                    society=society, venue=venue, booked_by=user, start=start, end=end
                )
                errors = run_rules(booking)
                if errors:
                    raise RulesFailed(errors, suggest_slots(booking))

                if venue.approval_needed():
                    booking.status = Booking.Status.PENDING  # waits in the admin queue
                else:
                    booking.status = Booking.Status.CONFIRMED  # auto-approved venues skip PENDING
                booking.save()
                booking.announce(user, None, booking.status)
        except IntegrityError:
            # The database safety net caught a clash the checks missed.
            raise BookingError("That slot was just taken. Please pick another time.")
        return booking

    @staticmethod
    def approve(booking_id, admin):
        if not _is_admin(admin):
            raise PermissionDenied("Only an admin can approve bookings.")
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=booking_id)
            booking.confirm(actor=admin)
        return booking

    @staticmethod
    def reject(booking_id, admin, reason):
        if not _is_admin(admin):
            raise PermissionDenied("Only an admin can reject bookings.")
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=booking_id)
            booking.reject(reason, actor=admin)
        return booking

    @staticmethod
    def cancel(booking_id, user):
        with transaction.atomic():
            booking = Booking.objects.select_for_update().select_related("society").get(pk=booking_id)
            if not (_is_admin(user) or booking.society.can_book(user)):
                raise PermissionDenied("You cannot cancel this booking.")
            booking.cancel(user)
        return booking
