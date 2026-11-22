from datetime import datetime

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from societies.models import Society
from venues.models import Venue


class StyledMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            cls = "form-select" if isinstance(f.widget, forms.Select) else "form-control"
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
