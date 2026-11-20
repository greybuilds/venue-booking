from datetime import date as date_cls, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
import json
from urllib.parse import parse_qs, urlparse

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from bookings.exceptions import BookingError, RulesFailed
from bookings.models import Booking
from bookings.services import BookingService
from societies.models import Society
from venues.models import Classroom, Lab, SeminarHall, Venue

from .forms import BookingForm, RejectForm, SignUpForm

KINDS = {"classroom": Classroom, "lab": Lab, "hall": SeminarHall}


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


def venue_detail(request, pk):
    venue = get_object_or_404(Venue, pk=pk)
    try:
        day = date_cls.fromisoformat(request.GET.get("date", ""))
    except ValueError:
        day = timezone.localdate()
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
    return render(request, "web/venue_detail.html", {
        "venue": venue, "kind": kind_of(venue), "day": day, "bars": bars, "hours": hours,
        "prev": day - timedelta(days=1), "next": day + timedelta(days=1),
        "extra": getattr(venue, "classroom", None) or getattr(venue, "lab", None) or getattr(venue, "seminarhall", None),
    })


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
def book(request):
    initial = {k: request.GET[k] for k in ("venue", "date", "start_time", "end_time", "society") if k in request.GET}
    form = BookingForm(request.POST or None, initial=initial, user=request.user)
    errors, suggestions = [], []
    can_book = form.fields["society"].queryset.exists()
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
    return render(request, "web/receipt.html", {"booking": booking})


@login_required
@require_POST
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if not (is_admin(request.user) or _my_bookings(request.user).filter(pk=pk).exists()):
        raise Http404
    try:
        booking.cancel(request.user)
        messages.success(request, "Booking cancelled.")
    except BookingError as e:
        messages.error(request, str(e))
    return redirect("booking_detail", pk=pk)


# ---- admin queue ----------------------------------------------------------

@admin_only
def manage(request):
    status = request.GET.get("status", "PENDING")
    qs = Booking.objects.select_related("venue", "society", "booked_by").order_by("start")
    if status in Booking.Status.values:
        qs = qs.filter(status=status)
    return render(request, "web/manage.html", {
        "bookings": qs, "status": status, "statuses": Booking.Status.choices,
        "pending_count": Booking.objects.filter(status="PENDING").count(),
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

    nxt = request.POST.get("next") or "manage"
    if request.headers.get("HX-Request") == "true":
        return _manage_htmx(request, booking, ok, msg, nxt)
    (messages.success if ok else messages.error)(request, msg)
    return redirect(nxt)


def _manage_htmx(request, booking, ok, msg, nxt):
    """Answer an in-place confirm/reject: the new row, or nothing if it no longer belongs in this list."""
    booking.refresh_from_db()
    shown = parse_qs(urlparse(nxt).query).get("status", ["PENDING"])[0]
    pending = Booking.objects.filter(status="PENDING").count()
    if not ok:
        resp = HttpResponse("")
        resp["HX-Reswap"] = "none"
    elif booking.status != shown:
        resp = HttpResponse("")
    else:
        resp = render(request, "web/partials/manage_row.html", {"b": booking, "next": nxt})
    resp["HX-Trigger"] = json.dumps({
        "toast": {"msg": msg, "type": "success" if ok else "error"},
        "pending": {"value": pending},
    })
    return resp


def not_found(request, exception):
    return render(request, "web/error.html", {"code": 404, "text": "That page doesn't exist."}, status=404)


def forbidden(request, exception):
    return render(request, "web/error.html", {"code": 403, "text": "You don't have access to that page."}, status=403)
