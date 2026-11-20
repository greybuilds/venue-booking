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
    path("bookings/", views.my_bookings, name="my_bookings"),
    path("bookings/<int:pk>/", views.booking_detail, name="booking_detail"),
    path("bookings/<int:pk>/receipt/", views.receipt, name="receipt"),
    path("bookings/<int:pk>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("manage/", views.manage, name="manage"),
    path("manage/<int:pk>/<str:action>/", views.manage_action, name="manage_action"),
]
