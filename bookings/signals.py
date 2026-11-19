from django.dispatch import Signal

# Sent (after the transaction commits) every time a booking is created or its status changes.
# This is the hook for Member 4: connect a receiver that writes an AuditEntry and
# calls the Notifier. Arguments:
#   sender      Booking
#   booking     the Booking instance
#   actor       the User who did it (or None for the daily job)
#   old_status  previous status, or None when the booking was just created
#   new_status  the new status
#   note        a reason or comment, may be ""
#
#   @receiver(status_changed)
#   def write_audit(sender, booking, actor, old_status, new_status, note, **kwargs): ...
status_changed = Signal()
