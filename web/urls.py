from django.contrib.auth import views as auth
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth.LoginView.as_view(authentication_form=LoginForm), name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    path("signup/", views.signup, name="signup"),
    path("venues/", views.venue_list, name="venue_list"),
    path("venues/<int:pk>/", views.venue_detail, name="venue_detail"),
    path("societies/", views.society_list, name="society_list"),
    path("societies/<int:pk>/", views.society_detail, name="society_detail"),
    path("book/", views.book, name="book"),
    path("book/info/", views.book_info, name="book_info"),
    path("bookings/", views.my_bookings, name="my_bookings"),
    path("bookings/<int:pk>/", views.booking_detail, name="booking_detail"),
    path("bookings/<int:pk>/receipt/", views.receipt, name="receipt"),
    path("bookings/<int:pk>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("manage/", views.manage, name="manage"),
    path("manage/<int:pk>/<str:action>/", views.manage_action, name="manage_action"),
    path("venues/add/<str:kind>/", views.venue_create, name="venue_create"),
    path("venues/<int:pk>/edit/", views.venue_edit, name="venue_edit"),
    path("availability/", views.availability, name="availability"),
    path("venues/<int:pk>/calendar/", views.venue_calendar, name="venue_calendar"),
    path("venues/<int:pk>/events/", views.venue_events, name="venue_events"),
    path("blocked-dates/add/", views.blocked_date_create, name="blocked_date_create"),
    path("blocked-dates/", views.blocked_date_list, name="blocked_date_list"),
    path("blocked-dates/<int:pk>/delete/", views.blocked_date_delete, name="blocked_date_delete"),
    path("calendar/", views.global_calendar, name="global_calendar"),
    path("calendar/events/", views.global_events, name="global_events"),
]
