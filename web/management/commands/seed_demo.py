from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from bookings.models import Booking
from societies.models import Society
from venues.models import Classroom, Lab, SeminarHall

DEMO_PASSWORD = "roomly-demo-123"  # local demo data only


class Command(BaseCommand):
    help = "Create demo users, a society, venues and a few bookings for local development."

    def handle(self, *args, **opts):
        def user(name, role, **kw):
            u, made = User.objects.get_or_create(username=name, defaults={"role": role, **kw})
            if made:
                u.set_password(DEMO_PASSWORD)
                u.save()
            return u

        admin = user("admin_demo", "ADMIN", is_staff=True, is_superuser=True)
        rep = user("rep_demo", "REP", first_name="Aisha", last_name="Khan")
        vp = user("vp_demo", "REP", first_name="Bilal", last_name="Raza")
        user("student_demo", "STUDENT")

        soc, _ = Society.objects.get_or_create(
            name="Coding Club", defaults={"is_verified": True, "president": rep, "vice_president": vp})
        Society.objects.get_or_create(
            name="Drama Society", defaults={"is_verified": False, "president": vp, "vice_president": rep})

        o, c = time(8), time(20)
        a, _ = Classroom.objects.get_or_create(name="Room A-101", defaults=dict(
            building="Academic Block A", floor=1, capacity=40, opens_at=o, closes_at=c, has_projector=True))
        b, _ = Lab.objects.get_or_create(name="CS Lab 2", defaults=dict(
            building="Computing Block", floor=2, capacity=30, opens_at=o, closes_at=c,
            requires_approval=True, equipment="30 PCs", supervisor="Dr. Malik"))
        h, _ = SeminarHall.objects.get_or_create(name="Main Seminar Hall", defaults=dict(
            building="Admin Block", floor=0, capacity=200, opens_at=o, closes_at=c,
            requires_approval=True, max_hours=6, av_kit="Projector, PA system"))

        tomorrow = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)
        if not Booking.objects.exists():
            Booking.objects.create(society=soc, venue=a, booked_by=rep, status="CONFIRMED",
                                   start=tomorrow.replace(hour=10), end=tomorrow.replace(hour=12))
            Booking.objects.create(society=soc, venue=b, booked_by=rep, status="PENDING",
                                   start=tomorrow.replace(hour=14), end=tomorrow.replace(hour=16))
        self.stdout.write(self.style.SUCCESS("Demo data ready. Users: admin_demo, rep_demo, vp_demo, student_demo."))
