from django.test import TestCase, TransactionTestCase
from xterm.consumers import XtermConsumer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from djangoWeb.asgi import application
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer



class XTermTest(TransactionTestCase):
    """
    pending django otp implementation
    """
    async def get_communicator(self, user):
        headers = await self.get_authenticated_headers(user)
        communicator = WebsocketCommunicator(
            application=application,
            path='/ws/xterm/',
            headers=headers
        )
        return communicator

    async def test_connections(self):
        superuser = await self.create_user(
            is_superuser=True,
            username='admin',
            email='test@test.com',
            password='test_pwd'
        )
        normal_user = await self.create_user(
            username='test user',
            email='test@test.com',
            password='test_pwd'
        )

        communicator = await self.get_communicator(superuser)

        connected, subprotocol = await communicator.connect()
        print(f'superuser {connected}, {subprotocol}')
        self.assertRaises(StopConsumer)
        self.assertEqual(connected, False)

        communicator = await self.get_communicator(normal_user)

        connected, subprotocol = await communicator.connect()
        print(f'user {connected}, {subprotocol}')
        self.assertRaises(StopConsumer)
        self.assertEqual(connected, False)


    async def get_authenticated_headers(self, user):
        """
        Helper method to create authentication headers for a given user.
        This simulates a logged-in session by attaching the session cookie.
        """

        @database_sync_to_async
        def _get_headers():
            from django.conf import settings
            from django.http import HttpRequest
            from django.contrib.auth import login
            from importlib import import_module
            from http.cookies import SimpleCookie

            # Create a fake request
            request = HttpRequest()
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore()
            login(request, user)

            # Save the session to get a session key
            request.session.save()

            # Create the session cookie
            session_cookie_name = settings.SESSION_COOKIE_NAME
            cookie_value = request.session.session_key
            cookies = SimpleCookie()
            cookies[session_cookie_name] = cookie_value
            cookie_header = cookies.output(header='', sep='; ').strip().encode()

            return [
                (b'cookie', cookie_header),
                (b'origin', b'http://testserver'),
            ]

        return await _get_headers()


    async def create_user(self, is_superuser=False, **credentials):
        """
        Helper method to create a superuser asynchronously.
        """

        @database_sync_to_async
        def _create_user():
            user = User.objects.create_superuser(**credentials) if is_superuser else User.objects.create_user(**credentials)
            return user

        return await _create_user()
