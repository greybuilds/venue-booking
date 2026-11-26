from datetime import date as date_cls, datetime, timedelta
from types import SimpleNamespace
from bookings.rules import OpeningHours, BlackoutDate
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
import json
from urllib.parse import parse_qs, urlparse

from django.http import Http404, HttpResponse, JsonResponse
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from bookings.exceptions import BookingError, RulesFailed
from bookings.models import Booking
from bookings.services import BookingService
from societies.models import Society
from venues.models import BlockedDate, Classroom, Lab, SeminarHall, Venue

from .forms import (
    BookingForm,
    RejectForm,
    SignUpForm,
    ClassroomForm,
    LabForm,
    SeminarHallForm,
    AvailabilityForm,
    BlockedDateForm,
)

KINDS = {"classroom": Classroom, "lab": Lab, "hall": SeminarHall}

VENUE_FORMS = {
    "classroom": ClassroomForm,
    "lab": LabForm,
    "hall": SeminarHallForm,
}

def is_admin(user):
    return user.is_authenticated and (user.role == "ADMIN" or user.is_superuser)


def admin_only(view):
    @login_required
    def wrapper(request, *a, **kw):
        if not is_admin(request.user):
            raise PermissionDenied("Admins only.")
        return view(request, *a, **kw)
    wrapper.__name__ = view.__name__
    return wrapper


def kind_of(venue):
    for label, model in KINDS.items():
        if model.objects.filter(pk=venue.pk).exists():
            return label
    return "venue"


# ---- public pages ---------------------------------------------------------

def home(request):
    return render(request, "pages/home.html", {
        "venues": Venue.objects.order_by("building", "name")[:6],
        "venue_count": Venue.objects.count(),
        "society_count": Society.objects.filter(is_verified=True).count(),
    })


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        messages.success(request, "Welcome aboard. Your account is ready.")
        return redirect("home")
    return render(request, "registration/signup.html", {"form": form})


def venue_list(request):
    qs = Venue.objects.order_by("building", "name")
    kind = request.GET.get("kind", "")
    if kind in KINDS:
        qs = qs.filter(pk__in=KINDS[kind].objects.values("pk"))
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(building__icontains=q))
    seats = request.GET.get("seats", "")
    if seats.isdigit():
        qs = qs.filter(capacity__gte=int(seats))
    venues = [(v, kind_of(v)) for v in qs]
    return render(request, "web/venue_list.html", {
        "venues": venues, "kind": kind, "q": q, "seats": seats,
    })


def availability(request):
    form = AvailabilityForm(request.GET or None)
    available_venues = []
    searched = bool(request.GET)

    if searched and form.is_valid():
        data = form.cleaned_data

        tz = timezone.get_current_timezone()
        start = timezone.make_aware(
            datetime.combine(data["date"], data["start_time"]), tz
        )
        end = timezone.make_aware(
            datetime.combine(data["date"], data["end_time"]), tz
        )

        kind = data.get("kind")
        seats = data.get("seats")

        if kind:
            venues = KINDS[kind].objects.all()
        else:
            venues = Venue.objects.all()

        if seats:
            venues = venues.filter(capacity__gte=seats)

        for venue in venues:
            candidate = SimpleNamespace(
                venue=venue,
                start=start,
                end=end,
            )

            try:
                OpeningHours().validate(candidate)
                BlackoutDate().validate(candidate)
            except BookingError:
                continue

            if venue.is_free(start, end):
                available_venues.append(venue)

    return render(request, "web/availability.html", {
        "form": form,
        "available_venues": available_venues,
        "searched": searched,
    })

@login_required
def venue_calendar(request, pk):
    venue = get_object_or_404(Venue, pk=pk)

    return render(request, "web/venue_calendar.html", {
        "venue": venue,
    })


@login_required
def venue_events(request, pk):
    venue = get_object_or_404(Venue, pk=pk)

    start_param = request.GET.get("start")
    end_param = request.GET.get("end")

    start = parse_datetime(start_param) if start_param else None
    end = parse_datetime(end_param) if end_param else None

    if not start or not end:
        return JsonResponse([], safe=False)

    if timezone.is_naive(start):
        start = timezone.make_aware(start)

    if timezone.is_naive(end):
        end = timezone.make_aware(end)

    events = []

    bookings = Booking.objects.filter(
        venue=venue,
        start__lt=end,
        end__gt=start,
        status__in=[
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
        ],
    )

    for booking in bookings:
        events.append({
            "title": "Booked",
            "start": booking.start.isoformat(),
            "end": booking.end.isoformat(),
        })

    blocked_dates = BlockedDate.objects.filter(
        start__lt=end,
        end__gt=start,
    ).filter(
        Q(venue__isnull=True) | Q(venue=venue)
    )

    for blocked in blocked_dates:
        venue_name = blocked.venue.name if blocked.venue else "All venues"

        events.append({
            "title": f"BLOCKED: {venue_name} - {blocked.reason}",
            "start": blocked.start.isoformat(),
            "end": blocked.end.isoformat(),
            "color": "#dc3545",
            "textColor": "#ffffff",
            "borderColor": "#b02a37",
            })

    return JsonResponse(events, safe=False)

@login_required
def global_calendar(request):
    venues = Venue.objects.all().order_by("name")

    return render(request, "web/global_calendar.html", {
        "venues": venues,
    })



@login_required
def global_events(request):
    start_param = request.GET.get("start")
    end_param = request.GET.get("end")
    venue_id = request.GET.get("venue", "").strip()

    start = parse_datetime(start_param) if start_param else None
    end = parse_datetime(end_param) if end_param else None

    if not start or not end:
        return JsonResponse([], safe=False)

    if timezone.is_naive(start):
        start = timezone.make_aware(start)

    if timezone.is_naive(end):
        end = timezone.make_aware(end)

    events = []

    # Get bookings across all venues
    bookings = Booking.objects.filter(
        start__lt=end,
        end__gt=start,
        status__in=[
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
        ],
    )

    # Filter bookings if a specific venue is selected
    if venue_id.isdigit():
        bookings = bookings.filter(venue_id=int(venue_id))

    bookings = bookings.select_related("venue")

    for booking in bookings:
        events.append({
            "title": f"{booking.venue.name} - Booked",
            "start": booking.start.isoformat(),
            "end": booking.end.isoformat(),
        })

    # Get blocked dates
    blocked_dates = BlockedDate.objects.filter(
        start__lt=end,
        end__gt=start,
    )

    # Include global blocks and selected venue's blocks
    if venue_id.isdigit():
        blocked_dates = blocked_dates.filter(
            Q(venue__isnull=True) | Q(venue_id=int(venue_id))
        )

    blocked_dates = blocked_dates.select_related("venue")

    for blocked in blocked_dates:
        venue_name = blocked.venue.name if blocked.venue else "All venues"

        events.append({
            "title": f"BLOCKED: {venue_name} - {blocked.reason}",
            "start": blocked.start.isoformat(),
            "end": blocked.end.isoformat(),
            "color": "#dc3545",
            "textColor": "#ffffff",
            "borderColor": "#b02a37",
        })

    return JsonResponse(events, safe=False)

def _day_bars(venue, day):
    """Booked bars and hour ticks for one venue on one day (shared by the venue page and /book/)."""
    tz = timezone.get_current_timezone()
    opens = timezone.make_aware(datetime.combine(day, venue.opens_at), tz)
    closes = timezone.make_aware(datetime.combine(day, venue.closes_at), tz)
    span = max((closes - opens).total_seconds(), 1)
    bookings = venue.bookings.filter(
        status__in=Booking.BLOCKING, start__lt=closes, end__gt=opens
    ).select_related("society")
    bars = []
    for b in bookings:
        left = max((b.start - opens).total_seconds(), 0) / span * 100
        right = min((b.end - opens).total_seconds(), span) / span * 100
        bars.append({"b": b, "left": round(left, 1), "width": round(right - left, 1)})
    hours = []
    h = opens.replace(minute=0, second=0)
    while h <= closes:
        if h >= opens:
            hours.append({"label": h.strftime("%H:%M"), "left": round((h - opens).total_seconds() / span * 100, 1)})
        h += timedelta(hours=1)
    return bars, hours


def venue_detail(request, pk):
    venue = get_object_or_404(Venue, pk=pk)
    try:
        day = date_cls.fromisoformat(request.GET.get("date", ""))
    except ValueError:
        day = timezone.localdate()
    bars, hours = _day_bars(venue, day)
    return render(request, "web/venue_detail.html", {
        "venue": venue, "kind": kind_of(venue), "day": day, "bars": bars, "hours": hours,
        "prev": day - timedelta(days=1), "next": day + timedelta(days=1),
        "extra": getattr(venue, "classroom", None) or getattr(venue, "lab", None) or getattr(venue, "seminarhall", None),
    })

@admin_only
def venue_create(request, kind):
    form_class = VENUE_FORMS.get(kind)

    if not form_class:
        raise Http404

    form = form_class(request.POST or None)

    if request.method == "POST" and form.is_valid():
        venue = form.save()
        messages.success(request, f"{venue.name} was added successfully.")
        return redirect("venue_detail", pk=venue.pk)

    return render(request, "web/venue_form.html", {
        "form": form,
        "kind": kind,
        "is_edit": False,
    })


@admin_only
def venue_edit(request, pk):
    venue = get_object_or_404(Venue, pk=pk)
    kind = kind_of(venue)
    form_class = VENUE_FORMS.get(kind)

    if not form_class:
        raise Http404

    if kind == "classroom":
        instance = venue.classroom
    elif kind == "lab":
        instance = venue.lab
    else:
        instance = venue.seminarhall

    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        venue = form.save()
        messages.success(request, f"{venue.name} was updated successfully.")
        return redirect("venue_detail", pk=venue.pk)

    return render(request, "web/venue_form.html", {
        "form": form,
        "kind": kind,
        "venue": venue,
        "is_edit": True,
    })

@admin_only
def blocked_date_create(request):
    if request.method == "POST":
        form = BlockedDateForm(request.POST)

        if form.is_valid():
            blocked_date = form.save(commit=False)
            blocked_date.created_by = request.user
            blocked_date.save()

            messages.success(request, "Blocked date added successfully.")

            if blocked_date.venue:
                return redirect("venue_calendar", pk=blocked_date.venue.pk)

            return redirect("venue_list")

    else:
        form = BlockedDateForm()

    return render(
        request,
        "web/blocked_date_form.html",
        {"form": form},
    )

@admin_only
def blocked_date_list(request):
    blocked_dates = BlockedDate.objects.select_related(
        "venue", "created_by"
    ).order_by("start")

    return render(
        request,
        "web/blocked_date_list.html",
        {"blocked_dates": blocked_dates},
    )


@admin_only
def blocked_date_delete(request, pk):
    blocked_date = get_object_or_404(BlockedDate, pk=pk)

    if request.method == "POST":
        blocked_date.delete()
        messages.success(request, "Blocked date deleted successfully.")
        return redirect("blocked_date_list")

    return redirect("blocked_date_list")

def society_list(request):
    return render(request, "web/society_list.html", {
        "societies": Society.objects.select_related("president", "vice_president").order_by("name"),
    })


def society_detail(request, pk):
    society = get_object_or_404(Society.objects.select_related("president", "vice_president"), pk=pk)
    upcoming = society.bookings.filter(
        status=Booking.Status.CONFIRMED, end__gte=timezone.now()
    ).select_related("venue")
    return render(request, "web/society_detail.html", {"society": society, "upcoming": upcoming})


# ---- booking --------------------------------------------------------------

@login_required
def book_info(request):
    """Rules and day timeline for the venue and date picked on /book/ (HTMX panel)."""
    venue = Venue.objects.filter(pk=request.GET.get("venue") or 0).first()
    try:
        day = date_cls.fromisoformat(request.GET.get("date", ""))
    except ValueError:
        day = timezone.localdate()
    ctx = {"venue": venue, "day": day}
    if venue:
        ctx["bars"], ctx["hours"] = _day_bars(venue, day)
    return render(request, "web/partials/book_info.html", ctx)


@login_required
def book(request):
    initial = {k: request.GET[k] for k in ("venue", "date", "start_time", "end_time", "society") if k in request.GET}
    form = BookingForm(request.POST or None, initial=initial, user=request.user)
    form.fields["date"].widget.attrs["min"] = timezone.localdate().isoformat()
    only = list(form.fields["society"].queryset[:2])
    if len(only) == 1 and "society" not in initial:
        form.fields["society"].initial = only[0].pk
        form.initial.setdefault("society", only[0].pk)
    errors, suggestions = [], []
    can_book = bool(only)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            booking = BookingService.request(d["society"], d["venue"], d["start"], d["end"], request.user)
        except RulesFailed as e:
            errors, suggestions = e.errors, e.suggestions
        except BookingError as e:
            errors = [str(e)]
        except PermissionDenied as e:
            errors = [str(e)]
        else:
            if booking.status == Booking.Status.CONFIRMED:
                messages.success(request, "Booked. Your slot is confirmed.")
            else:
                messages.info(request, "Request sent. An admin will confirm it soon.")
            return redirect("booking_detail", pk=booking.pk)
    return render(request, "web/book.html", {
        "form": form, "errors": errors, "suggestions": suggestions, "can_book": can_book,
        "venue_id": request.POST.get("venue") or request.GET.get("venue", ""),
        "date": request.POST.get("date") or request.GET.get("date", ""),
        "society_id": request.POST.get("society") or request.GET.get("society", ""),
    })


def _my_bookings(user):
    return Booking.objects.filter(
        Q(booked_by=user) | Q(society__president=user) | Q(society__vice_president=user)
    ).select_related("venue", "society").distinct()


@login_required
def my_bookings(request):
    now = timezone.now()
    qs = _my_bookings(request.user)
    return render(request, "web/my_bookings.html", {
        "upcoming": qs.filter(end__gte=now).exclude(
            status__in=["CANCELLED", "REJECTED", "EXPIRED", "COMPLETED"]).order_by("start"),
        "past": qs.exclude(pk__in=qs.filter(end__gte=now).exclude(
            status__in=["CANCELLED", "REJECTED", "EXPIRED", "COMPLETED"])).order_by("-start")[:30],
    })


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking.objects.select_related("venue", "society", "booked_by"), pk=pk)
    if not (is_admin(request.user) or _my_bookings(request.user).filter(pk=pk).exists()):
        raise Http404
    ctx = {"booking": booking, "can_cancel": booking.status in ("PENDING", "CONFIRMED")}
    if request.headers.get("HX-Request") == "true":
        return render(request, "web/partials/booking_sheet.html", ctx)
    return render(request, "web/booking_detail.html", ctx)


@login_required
def receipt(request, pk):
    booking = get_object_or_404(Booking.objects.select_related("venue", "society", "booked_by"), pk=pk)
    if not (is_admin(request.user) or _my_bookings(request.user).filter(pk=pk).exists()):
        raise Http404
    if booking.status not in ("CONFIRMED", "COMPLETED"):
        messages.info(request, "A receipt is only available once a booking is confirmed.")
        return redirect("booking_detail", pk=pk)
    hours = booking.duration.total_seconds() / 3600
    hours_label = f"{hours:g} hr{'s' if hours != 1 else ''}"
    return render(request, "web/receipt.html", {"booking": booking, "hours_label": hours_label})


@login_required
@require_POST
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if not (is_admin(request.user) or _my_bookings(request.user).filter(pk=pk).exists()):
        raise Http404
    ok, msg = True, "Booking cancelled."
    try:
        booking.cancel(request.user)
    except BookingError as e:
        ok, msg = False, str(e)
    if request.headers.get("HX-Request") == "true":
        # the bottom sheet: show the new state in place and let the list behind it refresh
        booking.refresh_from_db()
        resp = render(request, "web/partials/booking_sheet.html",
                      {"booking": booking, "can_cancel": booking.status in ("PENDING", "CONFIRMED")})
        resp["HX-Trigger"] = json.dumps({"toast": {"msg": msg, "type": "success" if ok else "error"}, "bookings-changed": True})
        return resp
    (messages.success if ok else messages.error)(request, msg)
    return redirect("booking_detail", pk=pk)


# ---- admin queue ----------------------------------------------------------

HISTORY = ("CANCELLED", "COMPLETED", "EXPIRED")


def _tab_counts():
    raw = {r["status"]: r["n"] for r in Booking.objects.values("status").annotate(n=Count("pk"))}
    return {
        "PENDING": raw.get("PENDING", 0), "CONFIRMED": raw.get("CONFIRMED", 0),
        "REJECTED": raw.get("REJECTED", 0), "HISTORY": sum(raw.get(s, 0) for s in HISTORY),
    }


@admin_only
def manage(request):
    status = request.GET.get("status", "PENDING")
    qs = Booking.objects.select_related("venue", "society", "booked_by").order_by("start")
    if status == "HISTORY" or status in HISTORY:
        qs = qs.filter(status__in=HISTORY)
        active = "HISTORY"
    else:
        if status not in Booking.Status.values:
            status = "PENDING"
        qs = qs.filter(status=status)
        active = status
    counts = _tab_counts()
    tabs = [(k, label, counts[k]) for k, label in
            (("PENDING", "Pending"), ("CONFIRMED", "Confirmed"), ("REJECTED", "Rejected"), ("HISTORY", "History"))]
    return render(request, "web/manage.html", {
        "bookings": qs, "status": active, "tabs": tabs, "pending_count": counts["PENDING"],
        "reject_form": RejectForm(),
    })


@admin_only
@require_POST
def manage_action(request, pk, action):
    booking = get_object_or_404(Booking, pk=pk)
    ok, msg = True, ""
    try:
        if action == "confirm":
            booking.confirm(request.user)
            msg = "Booking confirmed."
        elif action == "reject":
            form = RejectForm(request.POST)
            if not form.is_valid():
                ok, msg = False, "Give a reason when rejecting."
            else:
                booking.reject(form.cleaned_data["reason"], request.user)
                msg = "Booking rejected."
        else:
            raise Http404
    except BookingError as e:
        ok, msg = False, str(e)

    nxt = request.POST.get("next") or ""
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        nxt = "manage"
    if request.headers.get("HX-Request") == "true":
        return _manage_htmx(request, booking, ok, msg, nxt)
    (messages.success if ok else messages.error)(request, msg)
    return redirect(nxt)


def _manage_htmx(request, booking, ok, msg, nxt):
    """Answer an in-place confirm/reject: the new row, or nothing if it no longer belongs in this list."""
    booking.refresh_from_db()
    shown = parse_qs(urlparse(nxt).query).get("status", ["PENDING"])[0]
    counts = _tab_counts()
    pending = counts["PENDING"]
    if not ok:
        resp = HttpResponse("")
        resp["HX-Reswap"] = "none"
    elif booking.status != shown:
        resp = HttpResponse("")
    else:
        resp = render(request, "web/partials/manage_row.html", {"b": booking, "next": nxt})
    resp["HX-Trigger"] = json.dumps({
        "toast": {"msg": msg, "type": "success" if ok else "error"},
        "pending": {"value": pending, "counts": counts},
    })
    return resp


def _error(request, code, title, text, mood, retry=False):
    return render(request, "web/error.html", {"code": code, "title": title, "text": text, "mood": mood, "retry": retry}, status=code)


def not_found(request, exception):
    return _error(request, 404, "Page not found", "That page doesn't exist, or it has moved. Check the link, or head back to the venues.", "search")


def forbidden(request, exception):
    return _error(request, 403, "No access", "Your account can't open this page. If you think it should, ask an admin.", "block")


def bad_request(request, exception):
    return _error(request, 400, "Bad request", "We couldn't understand that request. Go back and try again.", "confused")


def csrf_failure(request, reason=""):
    return _error(request, 403, "Session expired", "Your form timed out or the page was open too long. Go back, reload the form and send it again.", "sleepy", retry=True)


def server_error(request):
    """Last resort: never let a broken template or database turn a 500 into a blank page."""
    try:
        return _error(request, 500, "Something broke", "That one is on us. Try again in a moment, and tell an admin if it keeps happening.", "dizzy", retry=True)
    except Exception:
        return HttpResponse(
            "<!doctype html><meta charset=utf-8><title>Something broke | Roomly</title>"
            "<body style=\"font-family:system-ui;max-width:32rem;margin:15vh auto;padding:0 1rem\">"
            "<h1 style=\"font-size:4rem;margin:0;color:#ff6a00\">500</h1><h2>Something broke</h2>"
            "<p>That one is on us. Try again in a moment.</p><p><a href=\"/\">Back home</a></p>",
            status=500,
        )
