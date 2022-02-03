from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser
from starlette.requests import HTTPConnection


class DiscordAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        if not conn.session.get('discord'):
            return

        return AuthCredentials(['authenticated']), SimpleUser(conn.session['user'])
