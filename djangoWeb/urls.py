"""
URL configuration for djangoWeb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django_otp.admin import OTPAdminSite
import django.contrib.auth.views as auth_views

admin.site.__class__ = OTPAdminSite


urlpatterns = [
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls, name="admin"),
    path('terminal/', include('xterm.urls')),
    path('filemanager/', include('file_manager.urls')),
    path('run_process/', include('run_process.urls')),
    path('', include('dashboard.urls'))
]
