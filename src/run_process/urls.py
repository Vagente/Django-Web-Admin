from django.urls import path

from . import views

app_name = "run_process"
urlpatterns = [
    path("", views.index, name="index"),
]
