from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .consumers import MAX_CONNECTION, CONNECTION_LIMIT_CODE
from django_otp.decorators import otp_required


@login_required()
@otp_required()
def index(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    context = {
        "MAX_CONNECTION": MAX_CONNECTION,
        "CONNECTION_LIMIT_CODE": CONNECTION_LIMIT_CODE
    }
    return render(request, 'xterm/index.html', context)
