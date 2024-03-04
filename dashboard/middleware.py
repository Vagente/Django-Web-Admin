from asgiref.sync import sync_to_async
from channels.middleware import BaseMiddleware
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.models import Device


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


class OTPAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        session = scope["session"]
        user = scope["user"]
        user.otp_device = None
        # user.is_verified = functools.partial(is_verified, user)
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
        user.is_verified = is_verified(user)
        return await super().__call__(scope, receive, send)
