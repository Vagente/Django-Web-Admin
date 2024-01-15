from django.contrib.auth.forms import AuthenticationForm
from django_otp.forms import OTPTokenForm


class LoginForm(AuthenticationForm):
    user_attr = AuthenticationForm.base_fields["username"].widget.attrs
    pass_attr = AuthenticationForm.base_fields["password"].widget.attrs
    user_attr.update({"class": 'form-control', 'placeholder': ""})
    pass_attr.update({"class": 'form-control', 'placeholder': ""})


class OTPForm(OTPTokenForm):
    OTPTokenForm.base_fields["otp_token"].widget.attrs.update({"class": 'form-control', 'placeholder': ""})
    OTPTokenForm.base_fields["otp_device"].widget.attrs.update({"class": "form-select form-select-sm"})

