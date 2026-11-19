from datetime import datetime, time, timedelta
from io import StringIO
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from societies.models import Society
from venues.models import Classroom, Lab

from .exceptions import BookingError, InvalidTransition, RulesFailed
from .models import Booking
from .rules import (
    BlackoutDate, MaxDuration, NoClash, OpeningHours, WeeklyQuota, overlaps, week_bounds,
)
from .services import BookingService
from .signals import status_changed

KHI = ZoneInfo("Asia/Karachi")
User = get_user_model()


def at(day, hour, minute=0):
    """Aware datetime in Karachi. day 0 = a Monday about two weeks from now."""
    today = timezone.localtime().date()
    monday = today + timedelta(days=14 - today.weekday())
    return datetime.combine(monday + timedelta(days=day), time(hour, minute), tzinfo=KHI)


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pres = User.objects.create_user("pres", password="x")
        cls.vp = User.objects.create_user("vp", password="x")
        cls.other = User.objects.create_user("other", password="x")
        cls.admin = User.objects.create_user("boss", password="x", role="ADMIN")
        cls.society = Society.objects.create(
            name="Drama Club", president=cls.pres, vice_president=cls.vp, is_verified=True
        )
        cls.society2 = Society.objects.create(
            name="Debate", president=cls.other, vice_president=cls.admin, is_verified=True
        )
        cls.hall = Classroom.objects.create(
            name="Hall A", building="Main", floor=1, capacity=100,
            opens_at=time(8), closes_at=time(20), max_hours=4, buffer_minutes=0,
        )
        cls.lab = Lab.objects.create(
            name="Lab 1", building="CS", floor=2, capacity=30,
            opens_at=time(9), closes_at=time(18), max_hours=3, requires_approval=True,
        )

    def make(self, start, end, venue=None, society=None, status=Booking.Status.CONFIRMED):
        b = Booking(society=society or self.society, venue=venue or self.hall,
                    booked_by=self.pres, start=start, end=end)
        b.status = status
        b.save()
        return b

    def candidate(self, start, end, venue=None, society=None):
        return Booking(society=society or self.society, venue=venue or self.hall,
                       booked_by=self.pres, start=start, end=end)


class OverlapFormulaTests(TestCase):
    def test_overlap(self):
        self.assertTrue(overlaps(2, 4, 3, 5))

    def test_back_to_back_is_not_overlap(self):
        self.assertFalse(overlaps(2, 4, 4, 6))

    def test_apart(self):
        self.assertFalse(overlaps(1, 2, 3, 4))

    def test_inside(self):
        self.assertTrue(overlaps(2, 6, 3, 4))

    def test_same_start_and_end(self):
        self.assertTrue(overlaps(2, 4, 2, 4))


class NoClashTests(Base):
    def setUp(self):
        self.make(at(1, 15), at(1, 17))

    def test_overlap_is_blocked(self):
        with self.assertRaises(BookingError):
            NoClash().validate(self.candidate(at(1, 16), at(1, 18)))

    def test_back_to_back_is_allowed(self):
        NoClash().validate(self.candidate(at(1, 17), at(1, 19)))
        NoClash().validate(self.candidate(at(1, 13), at(1, 15)))

    def test_inside_is_blocked(self):
        with self.assertRaises(BookingError):
            NoClash().validate(self.candidate(at(1, 15, 30), at(1, 16)))

    def test_same_start_and_end_is_blocked(self):
        with self.assertRaises(BookingError):
            NoClash().validate(self.candidate(at(1, 15), at(1, 17)))

    def test_other_venue_is_allowed(self):
        NoClash().validate(self.candidate(at(1, 15), at(1, 17), venue=self.lab))

    def test_cancelled_rejected_expired_free_the_slot(self):
        Booking.objects.all().delete()
        for st in ("CANCELLED", "REJECTED", "EXPIRED"):
            self.make(at(2, 10), at(2, 12), status=st)
        NoClash().validate(self.candidate(at(2, 10), at(2, 12)))

    def test_pending_blocks_the_slot(self):
        self.make(at(2, 10), at(2, 12), status=Booking.Status.PENDING)
        with self.assertRaises(BookingError):
            NoClash().validate(self.candidate(at(2, 11), at(2, 13)))

    def test_buffer_minutes(self):
        self.hall.buffer_minutes = 15
        self.hall.save()
        with self.assertRaises(BookingError):  # 5:00 pm start is inside the 15 min buffer
            NoClash().validate(self.candidate(at(1, 17), at(1, 19)))
        NoClash().validate(self.candidate(at(1, 17, 15), at(1, 19)))

    def test_editing_a_booking_does_not_clash_with_itself(self):
        b = Booking.objects.get()
        NoClash().validate(b)


class OtherRuleTests(Base):
    def test_opening_hours(self):
        OpeningHours().validate(self.candidate(at(1, 8), at(1, 10)))
        with self.assertRaises(BookingError):
            OpeningHours().validate(self.candidate(at(1, 7), at(1, 9)))
        with self.assertRaises(BookingError):
            OpeningHours().validate(self.candidate(at(1, 19), at(1, 21)))

    def test_booking_across_midnight_is_refused(self):
        with self.assertRaises(BookingError):
            OpeningHours().validate(self.candidate(at(1, 19), at(2, 1)))

    def test_max_duration(self):
        MaxDuration().validate(self.candidate(at(1, 9), at(1, 13)))
        with self.assertRaises(BookingError):
            MaxDuration().validate(self.candidate(at(1, 9), at(1, 14)))

    def test_weekly_quota(self):
        with self.settings(SOCIETY_WEEKLY_QUOTA_HOURS=6):
            self.make(at(0, 9), at(0, 13))  # 4 hours Monday
            WeeklyQuota().validate(self.candidate(at(2, 9), at(2, 11)))  # 4 + 2 = 6, ok
            with self.assertRaises(BookingError):
                WeeklyQuota().validate(self.candidate(at(2, 9), at(2, 12)))  # 7 > 6

    def test_weekly_quota_resets_next_week(self):
        with self.settings(SOCIETY_WEEKLY_QUOTA_HOURS=4):
            self.make(at(0, 9), at(0, 13))
            WeeklyQuota().validate(self.candidate(at(7, 9), at(7, 13)))

    def test_weekly_quota_is_per_society(self):
        with self.settings(SOCIETY_WEEKLY_QUOTA_HOURS=4):
            self.make(at(0, 9), at(0, 13))
            WeeklyQuota().validate(self.candidate(at(1, 9), at(1, 13), society=self.society2))

    def test_week_runs_monday_to_sunday(self):
        start, end = week_bounds(at(6, 23, 30))  # Sunday night
        self.assertEqual(start.weekday(), 0)
        self.assertEqual(end - start, timedelta(days=7))
        self.assertEqual(start, at(0, 0))

    def test_blackout_passes_until_member_3_adds_blocked_dates(self):
        BlackoutDate().validate(self.candidate(at(1, 9), at(1, 10)))


class StatusTests(Base):
    def pending(self):
        return self.make(at(1, 9), at(1, 11), status=Booking.Status.PENDING)

    def test_confirm(self):
        b = self.pending()
        b.confirm(self.admin)
        b.refresh_from_db()
        self.assertEqual(b.status, "CONFIRMED")

    def test_reject_needs_a_reason_and_stores_it(self):
        b = self.pending()
        with self.assertRaises(BookingError):
            b.reject("  ")
        b.reject("Hall under repair", self.admin)
        b.refresh_from_db()
        self.assertEqual((b.status, b.reason), ("REJECTED", "Hall under repair"))

    def test_rejected_can_never_become_confirmed(self):
        b = self.pending()
        b.reject("no", self.admin)
        with self.assertRaises(InvalidTransition):
            b.confirm(self.admin)

    def test_cancelled_is_final(self):
        b = self.pending()
        b.cancel(self.pres)
        for move in (b.confirm, lambda: b.reject("x"), b.mark_completed, b.mark_expired):
            with self.assertRaises(InvalidTransition):
                move()

    def test_pending_can_be_withdrawn_any_time(self):
        b = self.make(timezone.now() + timedelta(hours=1), timezone.now() + timedelta(hours=2),
                      status=Booking.Status.PENDING)
        b.cancel(self.pres)
        self.assertEqual(b.status, "CANCELLED")

    def test_confirmed_needs_24_hours_notice(self):
        soon = self.make(timezone.now() + timedelta(hours=5), timezone.now() + timedelta(hours=6))
        with self.assertRaises(BookingError):
            soon.cancel(self.pres)
        soon.cancel(self.admin)  # admins are exempt
        later = self.make(timezone.now() + timedelta(days=3), timezone.now() + timedelta(days=3, hours=1))
        later.cancel(self.pres)
        self.assertEqual(later.status, "CANCELLED")

    def test_completed_only_from_confirmed(self):
        with self.assertRaises(InvalidTransition):
            self.pending().mark_completed()

    def test_status_is_not_editable_in_forms(self):
        self.assertFalse(Booking._meta.get_field("status").editable)

    def test_signal_is_sent_after_commit(self):
        seen = []
        status_changed.connect(lambda **kw: seen.append((kw["old_status"], kw["new_status"])),
                               weak=False, dispatch_uid="t")
        try:
            b = self.pending()
            with self.captureOnCommitCallbacks(execute=True):
                b.confirm(self.admin)
        finally:
            status_changed.disconnect(dispatch_uid="t")
        self.assertEqual(seen, [("PENDING", "CONFIRMED")])

    def test_database_refuses_end_before_start(self):
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make(at(1, 11), at(1, 9))


class ServiceTests(Base):
    def test_only_president_or_vp_of_verified_society_can_book(self):
        BookingService.request(self.society, self.hall, at(1, 9), at(1, 10), self.vp)
        with self.assertRaises(PermissionDenied):
            BookingService.request(self.society, self.hall, at(2, 9), at(2, 10), self.other)
        self.society.is_verified = False
        self.society.save()
        with self.assertRaises(PermissionDenied):
            BookingService.request(self.society, self.hall, at(2, 9), at(2, 10), self.pres)

    def test_rep_swap_takes_effect_at_once(self):
        self.society.president = self.other
        self.society.save()
        with self.assertRaises(PermissionDenied):
            BookingService.request(self.society, self.hall, at(1, 9), at(1, 10), self.pres)

    def test_auto_approved_venue_skips_pending(self):
        b = BookingService.request(self.society, self.hall, at(1, 9), at(1, 10), self.pres)
        self.assertEqual(b.status, "CONFIRMED")

    def test_venue_needing_approval_goes_to_pending(self):
        b = BookingService.request(self.society, self.lab, at(1, 10), at(1, 11), self.pres)
        self.assertEqual(b.status, "PENDING")

    def test_clash_is_refused_cleanly(self):
        BookingService.request(self.society, self.hall, at(1, 9), at(1, 11), self.pres)
        with self.assertRaises(RulesFailed) as ctx:
            BookingService.request(self.society2, self.hall, at(1, 10), at(1, 12), self.other)
        self.assertIn("already booked", str(ctx.exception))
        self.assertEqual(Booking.objects.count(), 1)

    def test_all_problems_are_reported_at_once(self):
        with self.assertRaises(RulesFailed) as ctx:
            BookingService.request(self.society, self.hall, at(1, 6), at(1, 12), self.pres)
        self.assertGreaterEqual(len(ctx.exception.errors), 2)  # opens at 8, max 4 hours

    def test_nearby_free_slots_are_suggested(self):
        BookingService.request(self.society, self.hall, at(1, 9), at(1, 11), self.pres)
        with self.assertRaises(RulesFailed) as ctx:
            BookingService.request(self.society2, self.hall, at(1, 10), at(1, 12), self.other)
        self.assertTrue(ctx.exception.suggestions)
        for s, e in ctx.exception.suggestions:
            self.assertTrue(self.hall.is_free(s, e))

    def test_bad_times(self):
        for s, e in [(at(1, 11), at(1, 9)), (at(1, 9), at(1, 9)),
                     (datetime(2030, 1, 1, 9), datetime(2030, 1, 1, 10))]:
            with self.assertRaises(BookingError):
                BookingService.request(self.society, self.hall, s, e, self.pres)
        past = timezone.now() - timedelta(days=1)
        with self.assertRaises(BookingError):
            BookingService.request(self.society, self.hall, past, past + timedelta(hours=1), self.pres)

    def test_approve_and_reject_are_admin_only(self):
        b = BookingService.request(self.society, self.lab, at(1, 10), at(1, 11), self.pres)
        with self.assertRaises(PermissionDenied):
            BookingService.approve(b.pk, self.pres)
        BookingService.approve(b.pk, self.admin)
        b.refresh_from_db()
        self.assertEqual(b.status, "CONFIRMED")
        b2 = BookingService.request(self.society, self.lab, at(2, 10), at(2, 11), self.pres)
        with self.assertRaises(BookingError):
            BookingService.reject(b2.pk, self.admin, "")
        BookingService.reject(b2.pk, self.admin, "Lab closed")
        b2.refresh_from_db()
        self.assertEqual(b2.status, "REJECTED")

    def test_only_own_society_or_admin_can_cancel(self):
        b = BookingService.request(self.society, self.hall, at(5, 9), at(5, 10), self.pres)
        with self.assertRaises(PermissionDenied):
            BookingService.cancel(b.pk, self.other)
        BookingService.cancel(b.pk, self.vp)
        b.refresh_from_db()
        self.assertEqual(b.status, "CANCELLED")

    def test_rejected_slot_can_be_booked_again(self):
        b = BookingService.request(self.society, self.lab, at(1, 10), at(1, 11), self.pres)
        BookingService.reject(b.pk, self.admin, "no")
        BookingService.request(self.society2, self.lab, at(1, 10), at(1, 11), self.other)


class CloseBookingsTests(Base):
    def test_daily_job(self):
        past = timezone.now() - timedelta(days=2)
        done = self.make(past, past + timedelta(hours=1))
        stale = self.make(past, past + timedelta(hours=1), venue=self.lab, status=Booking.Status.PENDING)
        future = self.make(timezone.now() + timedelta(days=2), timezone.now() + timedelta(days=2, hours=1))
        out = StringIO()
        call_command("close_bookings", stdout=out)
        for b in (done, stale, future):
            b.refresh_from_db()
        self.assertEqual((done.status, stale.status, future.status), ("COMPLETED", "EXPIRED", "CONFIRMED"))
        self.assertIn("1 completed, 1 expired", out.getvalue())
