from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from .views import MyLoginView

app_name = "dashboard"
urlpatterns = [
    path("", views.index, name="index"),
    path("test/", views.test, name="test"),
    path("login/", MyLoginView.as_view(), name="login"),
    path("login/otp/", login_required(views.OTPView.as_view()), name="otp")
]
