from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Society(models.Model):
    """Minimal Society so Booking has something to point at.

    Written by Member 1 as a stub. Member 2 owns this app and will extend it
    (category, contact_email, faculty_advisor, verify(), swap_reps(), the
    registration form). Keep the name and signature of can_book(user): the
    BookingService calls it on every request.
    """

    name = models.CharField(max_length=120, unique=True)
    is_verified = models.BooleanField(default=False)
    president = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    vice_president = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        verbose_name_plural = "societies"

    def __str__(self):
        return self.name

    def clean(self):
        if self.president_id and self.president_id == self.vice_president_id:
            raise ValidationError("President and Vice President must be different people.")

    def can_book(self, user):
        """Only the President or VP of a VERIFIED society may book.

        Reads the database on every call: rights are never cached, so a rep
        swap takes effect immediately.
        """
        return self.is_verified and user.pk in (self.president_id, self.vice_president_id)
