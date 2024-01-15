from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from .views import MyLoginView

app_name = "dashboard"
urlpatterns = [
    path("", views.index, name="home"),
    path("test/", views.test, name="test"),
    path("login/", MyLoginView.as_view(), name="login"),
    path("login/otp/", login_required(views.OTPView.as_view()), name="otp")
]
