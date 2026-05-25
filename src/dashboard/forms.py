from django.contrib.auth.forms import AuthenticationForm
from django_otp.forms import OTPTokenForm
from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(AuthenticationForm):
    AuthenticationForm.base_fields["username"].widget.attrs.update({"class": 'form-control', 'placeholder': ""})
    AuthenticationForm.base_fields["password"].widget.attrs.update({"class": 'form-control', 'placeholder': ""})
    remember_me = forms.BooleanField(
        label=_("Remember Me"),
        label_suffix="",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )


class OTPForm(OTPTokenForm):
    OTPTokenForm.base_fields["otp_token"].widget.attrs.update({"class": 'form-control', 'placeholder': ""})
    OTPTokenForm.base_fields["otp_device"].widget.attrs.update({"class": "form-select form-select-sm"})
