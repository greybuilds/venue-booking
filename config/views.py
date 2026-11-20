from django.shortcuts import render

from venues.models import Venue


def home(request):
    venues = Venue.objects.order_by("building", "name")[:6]
    return render(request, "pages/home.html", {"venues": venues})
