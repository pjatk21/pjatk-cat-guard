import logging
import os

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from starlette.authentication import requires

from webpanel.common import templates
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from hikari import RESTApp

from shared.db import init_connection
from shared.documents import GuildConfiguration, VerificationRequest
from .endpoints import invites, general
from .middleware.auth import DiscordAuthBackend

load_dotenv()
init_connection()


oauth_discord = OAuth()
oauth_discord.register(
    'discord',
    client_id=os.getenv('DISCORD_CLIENT_ID'),
    client_secret=os.getenv('DISCORD_CLIENT_SECRET'),
    authorize_url="https://discord.com/api/oauth2/authorize",
    token_endpoint="https://discord.com/api/oauth2/token"
)

routes = [
    Route("/", general.AboutPage),
    Route("/verify/{secret}", invites.LoginQueueRequest),
    Route("/join/pjatk2021", invites.GuildInviteEndpoint),
    Mount("/static", app=StaticFiles(directory='webpanel/static'), name="static")
]

middleware = [
    Middleware(SessionMiddleware, secret_key=os.getenv('COOKIE_SECRET', 'someoneforgotcookiesecretrecipe')),
    Middleware(AuthenticationMiddleware, backend=DiscordAuthBackend())
]

if not os.getenv('COOKIE_SECRET'):
    logging.warning('Cookie secret hasn\'t been passed')

app = Starlette(routes=routes, middleware=middleware)


@app.route('/admin/login')
async def admin_login(request: Request):
    ds = oauth_discord.create_client('discord')
    redirect = request.url_for('admin_oauth')
    return await ds.authorize_redirect(request, redirect_uri=redirect, scope='identify email guilds guilds.members.read')


@app.route('/admin/oauth')
async def admin_oauth(request: Request):
    ds = oauth_discord.create_client('discord')
    token = await ds.authorize_access_token(request)
    async with RESTApp().acquire(token['access_token']) as client:
        user = await client.fetch_my_user()

        available_guilds = [guild.id for guild in await client.fetch_my_guilds() if GuildConfiguration.objects(guild_id=guild.id).first()]

        if not len(available_guilds):
            return JSONResponse({'message': 'not in guilds'})

        request.session['discord'] = token
        request.session['user'] = str(user)
        request.session['guilds'] = available_guilds

    return RedirectResponse(request.url_for('admin_index'))


@requires(['authenticated'])
@app.route('/admin/logout')
async def admin_logout(request: Request):
    del request.session['discord']
    del request.session['user']
    return PlainTextResponse('Wylogowano')


@requires(['authenticated'], redirect='admin_login')
@app.route('/admin/')
async def admin_index(request: Request):
    async with RESTApp().acquire(request.session['discord']['access_token']) as client:
        awaiting = VerificationRequest.objects()
        print(awaiting)
        # guilds = [(guild.name, guild.id) for guild in await client.fetch_my_guilds() if guild.id in request.session['guilds']]
        return templates.TemplateResponse('admin/base.html', {'request': request, 'awaiting': awaiting})


@app.route('/gate')
async def verify_gate(request: Request):
    return templates.TemplateResponse('upload.html', {"request": request})
