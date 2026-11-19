class BookingError(Exception):
    """A booking cannot be made or changed. str(error) is a clear reason for the user."""


class InvalidTransition(BookingError):
    """A status change that is not allowed, e.g. confirming a REJECTED booking."""


class RulesFailed(BookingError):
    """One or more booking rules failed.

    errors:      list of clear reasons, one per failed rule
    suggestions: list of (start, end) tuples, nearby free slots at the same venue
    """

    def __init__(self, errors, suggestions=None):
        self.errors = list(errors)
        self.suggestions = list(suggestions or [])
        super().__init__("; ".join(self.errors))
