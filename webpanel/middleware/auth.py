from starlette.authentication import AuthenticationBackend
from starlette.requests import HTTPConnection


class DiscordAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        if not conn.session.get('discord'):
            return

