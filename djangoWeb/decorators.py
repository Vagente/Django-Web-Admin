from functools import wraps
from django.core.exceptions import PermissionDenied


def staff_required():
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_view(request, *args, **kwargs):
            if request.user.is_staff:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('You need to be superuser to view this page')

        return _wrapper_view

    return decorator
