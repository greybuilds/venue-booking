from datetime import datetime

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from societies.models import Society
from venues.models import BlockedDate, Venue, Classroom, Lab, SeminarHall


class StyledMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields.values():
            if isinstance(f.widget, forms.Select):
                cls = "form-select"
            elif isinstance(f.widget, forms.CheckboxInput):
                cls = "form-check-input"
            else:
                cls = "form-control"

            f.widget.attrs.setdefault("class", cls)

class LoginForm(StyledMixin, AuthenticationForm):
    pass


class SignUpForm(StyledMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone")


class BookingForm(StyledMixin, forms.Form):
    society = forms.ModelChoiceField(queryset=Society.objects.none())
    venue = forms.ModelChoiceField(queryset=Venue.objects.order_by("building", "name"))
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["society"].queryset = Society.objects.filter(
            Q(president=user) | Q(vice_president=user), is_verified=True
        )

    def clean(self):
        data = super().clean()
        d, s, e = data.get("date"), data.get("start_time"), data.get("end_time")
        if d and s and e:
            tz = timezone.get_current_timezone()
            data["start"] = timezone.make_aware(datetime.combine(d, s), tz)
            data["end"] = timezone.make_aware(datetime.combine(d, e), tz)
        return data


class RejectForm(StyledMixin, forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}))


class ClassroomForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Classroom
        fields = [
            "name",
            "building",
            "floor",
            "capacity",
            "opens_at",
            "closes_at",
            "requires_approval",
            "max_hours",
            "buffer_minutes",
            "has_projector",
        ]


class LabForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Lab
        fields = [
            "name",
            "building",
            "floor",
            "capacity",
            "opens_at",
            "closes_at",
            "requires_approval",
            "max_hours",
            "buffer_minutes",
            "equipment",
            "supervisor",
        ]


class SeminarHallForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = SeminarHall
        fields = [
            "name",
            "building",
            "floor",
            "capacity",
            "opens_at",
            "closes_at",
            "requires_approval",
            "max_hours",
            "buffer_minutes",
            "av_kit",
        ]

class AvailabilityForm(StyledMixin, forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time"})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time"})
    )
    kind = forms.ChoiceField(
        choices=[
            ("", "All types"),
            ("classroom", "Classrooms"),
            ("lab", "Labs"),
            ("hall", "Seminar halls"),
        ],
        required=False,
    )
    seats = forms.IntegerField(
        min_value=1,
        required=False,
        label="Minimum capacity",
    )

    def clean(self):
        data = super().clean()

        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", "End time must be after start time.")

        return data

class BlockedDateForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = BlockedDate
        fields = ["venue", "start", "end", "reason"]
        widgets = {
            "start": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["venue"].required = False
        self.fields["venue"].empty_label = "All venues"
    def clean(self):
        data = super().clean()

        start = data.get("start")
        end = data.get("end")

        if start and end and end <= start:
            self.add_error("end", "End time must be after start time.")

        return data