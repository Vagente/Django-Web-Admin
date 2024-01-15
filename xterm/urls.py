from django.urls import path

from . import views

app_name = "xterm"
urlpatterns = [
    path("", views.index, name="index"),
]
