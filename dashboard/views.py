from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from functools import partial
from django.contrib.auth import BACKEND_SESSION_KEY
from django.contrib.auth import views as auth_views
from django.utils.functional import cached_property
from .forms import OTPForm
from django_otp.decorators import otp_required
from .forms import LoginForm


@login_required()
def index(request):
    return render(request, 'dashboard/index.html')


@otp_required()
def test(request):
    return render(request, 'dashboard/test.html')


class OTPView(auth_views.LoginView):
    otp_token_form = OTPForm
    template_name = "registration/otp.html"

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
