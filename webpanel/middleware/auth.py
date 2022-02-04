from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser
from starlette.requests import HTTPConnection


class DiscordAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        if not conn.session.get('discord') or not conn.session.get('user'):
            return

        return AuthCredentials(['authenticated']), SimpleUser(conn.session['user'])
