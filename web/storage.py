import os

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage


class VersionedStaticStorage(StaticFilesStorage):
    """Adds ?v=<file modified time> to static URLs.

    The number changes whenever a file changes, so browsers fetch the new
    CSS and JS on their own and nobody has to hard reload.
    """

    def url(self, name):
        url = super().url(name)
        path = finders.find(name)
        if not path:
            try:
                path = self.path(name)
            except Exception:
                return url
        try:
            return f"{url}?v={int(os.path.getmtime(path))}"
        except OSError:
            return url
