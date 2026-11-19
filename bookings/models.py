from datetime import timedelta

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models, transaction
from django.db.models import F, Func, Q
from django.utils import timezone

from .exceptions import BookingError, InvalidTransition
from .signals import status_changed

# Cancelling a CONFIRMED booking needs this much notice (admins are exempt).
CANCEL_NOTICE = timedelta(hours=24)


class TsTzRange(Func):
    """start, end -> a PostgreSQL time range [start, end). Half open, so back to back is fine."""

    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"
        EXPIRED = "EXPIRED", "Expired"

    # Statuses that hold the slot. REJECTED, CANCELLED and EXPIRED free it.
    BLOCKING = (Status.PENDING, Status.CONFIRMED)

    # The only moves that are allowed. Anything else raises InvalidTransition.
    ALLOWED = {
        Status.PENDING: {Status.CONFIRMED, Status.REJECTED, Status.CANCELLED, Status.EXPIRED},
        Status.CONFIRMED: {Status.CANCELLED, Status.COMPLETED},
    }

    society = models.ForeignKey(
        "societies.Society", on_delete=models.PROTECT, related_name="bookings"
    )
    venue = models.ForeignKey(
        "venues.Venue", on_delete=models.PROTECT, related_name="bookings"
    )
    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings"
    )
    start = models.DateTimeField()
    end = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, editable=False
    )
    reason = models.TextField(blank=True, help_text="Why it was rejected or cancelled.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end__gt=F("start")), name="booking_end_after_start"
            ),
            # Last safety net: even a bug in our code cannot create an overlap. Only
            # PENDING and CONFIRMED bookings hold the slot, so the others do not count.
            ExclusionConstraint(
                name="no_overlapping_bookings",
                expressions=[
                    ("venue", RangeOperators.EQUAL),
                    (TsTzRange("start", "end"), RangeOperators.OVERLAPS),
                ],
                condition=Q(status__in=["PENDING", "CONFIRMED"]),
            ),
        ]
        indexes = [models.Index(fields=["venue", "start"], name="booking_venue_start_idx")]

    def __str__(self):
        return f"{self.society} @ {self.venue} {self.start:%Y-%m-%d %H:%M} ({self.status})"

    @property
    def duration(self):
        return self.end - self.start

    @property
    def blocks_slot(self):
        return self.status in self.BLOCKING

    # ---- status changes: the ONLY way to change self.status ----------------

    def confirm(self, actor=None):
        self._move(self.Status.CONFIRMED, actor)

    def reject(self, reason, actor=None):
        if not reason or not reason.strip():
            raise BookingError("A reason is required to reject a booking.")
        self._move(self.Status.REJECTED, actor, reason.strip())

    def cancel(self, by):
        """Cancel (or withdraw, if still PENDING).

        A CONFIRMED booking needs 24 hours notice, unless an admin cancels it.
        """
        is_admin = getattr(by, "role", None) == "ADMIN" or getattr(by, "is_superuser", False)
        if (
            self.status == self.Status.CONFIRMED
            and not is_admin
            and self.start - timezone.now() < CANCEL_NOTICE
        ):
            raise BookingError("A confirmed booking needs at least 24 hours notice to cancel.")
        self._move(self.Status.CANCELLED, by)

    def mark_completed(self):
        self._move(self.Status.COMPLETED, None)

    def mark_expired(self):
        self._move(self.Status.EXPIRED, None)

    def _move(self, new, actor, note=""):
        old = self.status
        if new not in self.ALLOWED.get(old, set()):
            raise InvalidTransition(f"{old} -> {new}")
        self.status = new
        if new in (self.Status.REJECTED, self.Status.CANCELLED) and note:
            self.reason = note
        self.save(update_fields=["status", "reason"])
        self.announce(actor, old, new, note)

    def announce(self, actor, old, new, note=""):
        """Tell the audit log and the Notifier (Member 4) once the transaction commits."""
        transaction.on_commit(
            lambda: status_changed.send(
                sender=Booking,
                booking=self,
                actor=actor,
                old_status=old,
                new_status=new,
                note=note,
            )
        )
