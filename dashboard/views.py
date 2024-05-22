from functools import partial

import os
import psutil
from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from .forms import LoginForm
from .forms import OTPForm


@login_required()
def index(request):
    load = os.getloadavg()
    load = [round(i, 4) for i in load]
    context = {
        "boot_time": psutil.boot_time(),
        "time_zone": settings.TIME_ZONE,
        "load_avg": f"{load[0]}, {load[1]}, {load[2]}"
    }
    return render(request, 'dashboard/index.html', context)


class OTPView(auth_views.LoginView):
    otp_token_form = OTPForm
    template_name = "registration/otp.html"
    redirect_verified_user = True

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_verified_user and self.request.user.is_verified():
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a OTP page."
                )
            return HttpResponseRedirect(redirect_to)
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def authentication_form(self):
        user = self.request.user
        form = partial(self.otp_token_form, user)
        return form

    def form_valid(self, form):
        # OTPTokenForm does not call authenticate(), so we may need to populate
        # user.backend ourselves to keep login() happy.
        user = form.get_user()
        if not hasattr(user, 'backend'):
            user.backend = self.request.session[BACKEND_SESSION_KEY]
        return super().form_valid(form)


class MyLoginView(auth_views.LoginView):
    redirect_authenticated_user = True
    authentication_form = LoginForm

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        auth_login(self.request, form.get_user())
        if not form.cleaned_data["remember_me"]:
            self.request.session.set_expiry(5)
        return HttpResponseRedirect(self.get_success_url())
