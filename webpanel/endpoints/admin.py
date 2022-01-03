import os

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, PlainTextResponse
from starlette.routing import Route

# from webpanel.common import discord_oauth

from aiohttp import ClientSession


class AdminDiscordLogin(HTTPEndpoint):
    async def get(self, request: Request):
        return RedirectResponse(
            os.getenv('DISCORD_REDIRECT')
        )


class AdminDiscordCallback(HTTPEndpoint):
    async def get(self, request: Request):
        async with ClientSession() as client:
            async with client.post('https://discord.com/api/v8/oauth2/token', data={
                'code': request.query_params.get('code'),
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'redi': ''
            }) as response:
                pass
        return PlainTextResponse()


routes = [
    Route("/login", AdminDiscordLogin),
    Route("/oauth2", AdminDiscordCallback)
]
