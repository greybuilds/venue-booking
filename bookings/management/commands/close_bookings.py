from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking


class Command(BaseCommand):
    help = "Daily job: CONFIRMED bookings past their end become COMPLETED; PENDING ones whose start has passed become EXPIRED."

    def handle(self, *args, **options):
        now = timezone.now()
        done = expired = 0
        with transaction.atomic():
            for b in Booking.objects.select_for_update().filter(status=Booking.Status.CONFIRMED, end__lt=now):
                b.mark_completed()
                done += 1
            for b in Booking.objects.select_for_update().filter(status=Booking.Status.PENDING, start__lt=now):
                b.mark_expired()
                expired += 1
        self.stdout.write(f"{done} completed, {expired} expired")
