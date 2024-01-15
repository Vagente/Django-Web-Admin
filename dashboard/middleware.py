from channels.middleware import BaseMiddleware

import functools
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.models import Device
from asgiref.sync import sync_to_async


def is_verified(user):
    return user.otp_device is not None


@sync_to_async
def _device_from_persistent_id(persistent_id):
    # Convert legacy persistent_id values (these used to be full import
    # paths). This won't work for apps with models in sub-modules, but that
    # should be pretty rare. And the worst that happens is the user has to
    # log in again.
    if persistent_id.count('.') > 1:
        parts = persistent_id.split('.')
        persistent_id = '.'.join((parts[-3], parts[-1]))

    device = Device.from_persistent_id(persistent_id)

    return device


# @database_sync_to_async
# def get_user(scope):
#     """
#     Return the user model instance associated with the given scope.
#     If no user is retrieved, return an instance of `AnonymousUser`.
#     """
#     # postpone model import to avoid ImproperlyConfigured error before Django
#     # setup is complete.
#     from django.contrib.auth.models import AnonymousUser
#
#     if "session" not in scope:
#         raise ValueError(
#             "Cannot find session in scope. You should wrap your consumer in "
#             "SessionMiddleware."
#         )
#     session = scope["session"]
#     user = None
#     try:
#         user_id = _get_user_session_key(session)
#         backend_path = session[BACKEND_SESSION_KEY]
#     except KeyError:
#         pass
#     else:
#         if backend_path in settings.AUTHENTICATION_BACKENDS:
#             backend = load_backend(backend_path)
#             user = backend.get_user(user_id)
#             # Verify the session
#             if hasattr(user, "get_session_auth_hash"):
#                 session_hash = session.get(HASH_SESSION_KEY)
#                 session_hash_verified = session_hash and constant_time_compare(
#                     session_hash, user.get_session_auth_hash()
#                 )
#                 if not session_hash_verified:
#                     session.flush()
#                     user = None
#
#     if user is not None:
#         user.otp_device = None
#         user.is_verified = functools.partial(is_verified, user)
#         if user.is_authenticated:
#             persistent_id = session.get(DEVICE_ID_SESSION_KEY)
#             print("debug")
#             print(persistent_id)
#             device = (
#                 _device_from_persistent_id(persistent_id)
#                 if persistent_id
#                 else None
#             )
#             if (device is not None) and (device.user_id != user.pk):
#                 device = None
#             if (device is None) and (DEVICE_ID_SESSION_KEY in session):
#                 del session[DEVICE_ID_SESSION_KEY]
#             user.otp_device = device
#             return user
#     return AnonymousUser()


class OTPAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        session = scope["session"]

        user = scope["user"]
        user.otp_device = None
        user.is_verified = functools.partial(is_verified, user)
        if user.is_authenticated:
            persistent_id = session.get(DEVICE_ID_SESSION_KEY)
            device = (
                await _device_from_persistent_id(persistent_id)
                if persistent_id
                else None
            )
            if (device is not None) and (device.user_id != user.pk):
                device = None
            if (device is None) and (DEVICE_ID_SESSION_KEY in session):
                del session[DEVICE_ID_SESSION_KEY]
            user.otp_device = device
        return await super().__call__(scope, receive, send)
