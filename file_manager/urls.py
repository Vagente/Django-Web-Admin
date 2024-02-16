from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = "file_manager"
urlpatterns = [
    path("", views.file_manager, name="index")
]
