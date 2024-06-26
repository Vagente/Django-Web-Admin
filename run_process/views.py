from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django_otp.decorators import otp_required
from djangoWeb.decorators import staff_required
from . import *


@staff_required()
@otp_required()
def index(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    context = {
        "MAX_CONNECTION": XTERM_MAX_CONNECTION,
        "CONNECTION_LIMIT_CODE": XTERM_CONNECTION_LIMIT_CODE,
        "JSON_TYPE": JSON_TYPE,
        "TYPE_PTY_INPUT": TYPE_PTY_INPUT,
        "TYPE_PTY_OUTPUT": TYPE_PTY_OUTPUT,
        "TYPE_RESIZE": TYPE_RESIZE,
        "TYPE_INIT": TYPE_INIT,
        "JSON_CONTENT": JSON_CONTENT,
        "TYPE_EXITED": TYPE_EXITED,
        "TYPE_ERROR": TYPE_ERROR,
        "JOURNALCTL": JOURNALCTL
    }
    return render(request, 'run_process/index.html', context)
