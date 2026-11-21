from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from bookings.models import Booking
from societies.models import Society
from venues.models import Classroom, Lab


class WebPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rep = User.objects.create_user("rep", password="x", role="REP")
        cls.vp = User.objects.create_user("vp", password="x", role="REP")
        cls.student = User.objects.create_user("stu", password="x")
        cls.admin = User.objects.create_user("adm", password="x", role="ADMIN")
        cls.soc = Society.objects.create(name="Chess", is_verified=True, president=cls.rep, vice_president=cls.vp)
        cls.room = Classroom.objects.create(name="R1", building="B", floor=1, capacity=30,
                                            opens_at=time(0, 0), closes_at=time(23, 59))
        cls.lab = Lab.objects.create(name="L1", building="B", floor=2, capacity=20,
                                     opens_at=time(0, 0), closes_at=time(23, 59), requires_approval=True)

    def slot(self, days=3, hour=10):
        d = (timezone.localtime() + timedelta(days=days)).date()
        return {"date": d.isoformat(), "start_time": f"{hour:02d}:00", "end_time": f"{hour + 1:02d}:00"}

    def test_public_pages_load(self):
        for name, args in [("home", []), ("venue_list", []), ("venue_detail", [self.room.pk]),
                           ("society_list", []), ("society_detail", [self.soc.pk]),
                           ("login", []), ("signup", [])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)

    def test_venue_filter(self):
        r = self.client.get(reverse("venue_list"), {"kind": "lab"})
        self.assertContains(r, "L1")
        self.assertNotContains(r, "R1")

    def test_private_pages_need_login(self):
        for name in ("book", "my_bookings", "manage"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_student_sees_warning_and_cannot_book(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse("book")), "Only the President or VP")

    def test_rep_books_instant_venue(self):
        self.client.force_login(self.rep)
        r = self.client.post(reverse("book"), {"society": self.soc.pk, "venue": self.room.pk, **self.slot()})
        b = Booking.objects.get()
        self.assertRedirects(r, reverse("booking_detail", args=[b.pk]))
        self.assertEqual(b.status, "CONFIRMED")
        self.assertEqual(self.client.get(reverse("receipt", args=[b.pk])).status_code, 200)

    def test_clash_shows_reason_and_suggestions(self):
        self.client.force_login(self.rep)
        data = {"society": self.soc.pk, "venue": self.room.pk, **self.slot()}
        self.client.post(reverse("book"), data)
        r = self.client.post(reverse("book"), data)
        self.assertContains(r, "That booking can")
        self.assertContains(r, "nearby slots are free")

    def test_admin_confirms_and_reject_needs_reason(self):
        self.client.force_login(self.rep)
        self.client.post(reverse("book"), {"society": self.soc.pk, "venue": self.lab.pk, **self.slot()})
        b = Booking.objects.get()
        self.assertEqual(b.status, "PENDING")
        self.assertEqual(self.client.get(reverse("manage")).status_code, 403)
        self.client.force_login(self.admin)
        self.client.post(reverse("manage_action", args=[b.pk, "reject"]), {"reason": ""})
        b.refresh_from_db(); self.assertEqual(b.status, "PENDING")
        self.client.post(reverse("manage_action", args=[b.pk, "confirm"]))
        b.refresh_from_db(); self.assertEqual(b.status, "CONFIRMED")

    def test_other_users_cannot_open_a_booking(self):
        self.client.force_login(self.rep)
        self.client.post(reverse("book"), {"society": self.soc.pk, "venue": self.room.pk, **self.slot()})
        b = Booking.objects.get()
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("booking_detail", args=[b.pk])).status_code, 404)

    def test_cancel_by_vp(self):
        self.client.force_login(self.rep)
        self.client.post(reverse("book"), {"society": self.soc.pk, "venue": self.room.pk, **self.slot()})
        b = Booking.objects.get()
        self.client.force_login(self.vp)
        self.client.post(reverse("cancel_booking", args=[b.pk]))
        b.refresh_from_db(); self.assertEqual(b.status, "CANCELLED")


class HtmxTests(TestCase):
    """In-place swaps: same rules as the full-page paths, different response shape."""
    setUpTestData = classmethod(WebPagesTests.setUpTestData.__func__)
    slot = WebPagesTests.slot

    def pending_booking(self):
        self.client.force_login(self.rep)
        self.client.post(reverse("book"), {"society": self.soc.pk, "venue": self.lab.pk, **self.slot()})
        return Booking.objects.get()

    def test_confirm_removes_row_from_pending_list_and_sends_toast(self):
        b = self.pending_booking()
        self.client.force_login(self.admin)
        r = self.client.post(reverse("manage_action", args=[b.pk, "confirm"]), {"next": "/manage/?status=PENDING"},
                             headers={"HX-Request": "true"})
        b.refresh_from_db(); self.assertEqual(b.status, "CONFIRMED")
        self.assertEqual(r.content, b"")
        self.assertIn('"type": "success"', r["HX-Trigger"])
        self.assertIn('"pending": {"value": 0}', r["HX-Trigger"])

    def test_htmx_error_swaps_nothing(self):
        b = self.pending_booking()
        self.client.force_login(self.admin)
        r = self.client.post(reverse("manage_action", args=[b.pk, "reject"]), {"reason": "", "next": "/manage/"},
                             headers={"HX-Request": "true"})
        self.assertEqual(r["HX-Reswap"], "none")
        self.assertIn('"type": "error"', r["HX-Trigger"])
        b.refresh_from_db(); self.assertEqual(b.status, "PENDING")

    def test_detail_returns_sheet_partial_for_htmx(self):
        b = self.pending_booking()
        r = self.client.get(reverse("booking_detail", args=[b.pk]), headers={"HX-Request": "true"})
        self.assertTemplateUsed(r, "web/partials/booking_sheet.html")
        self.assertNotContains(r, "<html")

    def test_cancel_from_sheet_swaps_sheet_and_refreshes_list(self):
        b = self.pending_booking()
        r = self.client.post(reverse("cancel_booking", args=[b.pk]), headers={"HX-Request": "true"})
        b.refresh_from_db(); self.assertEqual(b.status, "CANCELLED")
        self.assertTemplateUsed(r, "web/partials/booking_sheet.html")
        self.assertIn("bookings-changed", r["HX-Trigger"])
        self.assertIn('"type": "success"', r["HX-Trigger"])

    def test_manage_action_ignores_offsite_next(self):
        b = self.pending_booking()
        self.client.force_login(self.admin)
        r = self.client.post(reverse("manage_action", args=[b.pk, "confirm"]), {"next": "https://evil.example/x"})
        self.assertRedirects(r, reverse("manage"))


class ErrorPageTests(TestCase):
    """Every error a visitor can hit shows our page, never a bare Django one."""
    def test_404(self):
        r = self.client.get("/definitely-not-here/")
        self.assertEqual(r.status_code, 404); self.assertContains(r, "Page not found", status_code=404)

    def test_403_for_anonymous_on_admin_page(self):
        r = self.client.get(reverse("manage"), follow=False)
        self.assertIn(r.status_code, (302, 403))

    def test_csrf_failure_uses_our_page(self):
        from django.test import Client
        r = Client(enforce_csrf_checks=True).post(reverse("login"), {"username": "x", "password": "y"})
        self.assertContains(r, "Session expired", status_code=403)

    def test_500_page(self):
        from django.test import Client
        from django.urls import path
        c = Client(raise_request_exception=False)
        with self.settings(ROOT_URLCONF="web.tests_urls"):
            r = c.get("/boom/")
        self.assertContains(r, "Something broke", status_code=500)
