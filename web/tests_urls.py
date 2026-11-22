"""URLconf used only by ErrorPageTests: one view that always crashes."""
from django.urls import path
from config.urls import urlpatterns as base, handler404, handler403, handler400, handler500  # noqa: F401


def boom(request):
    raise RuntimeError("boom")


urlpatterns = [path("boom/", boom)] + base
