import os

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from hikari import RESTApp
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, PlainTextResponse

from shared.db import init_connection
from shared.documents import VerificationRequest, GuildConfiguration
from webpanel.common import templates
from webpanel.middleware.auth import DiscordAuthBackend

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

middleware = [
    Middleware(SessionMiddleware, secret_key=os.getenv('COOKIE_SECRET', 'someoneforgotcookiesecretrecipe')),
    Middleware(AuthenticationMiddleware, backend=DiscordAuthBackend())
]

app = Starlette(middleware=middleware)


@app.route('/login')
async def admin_login(request: Request):
    ds = oauth_discord.create_client('discord')
    redirect = request.url_for('admin:admin_oauth')
    return await ds.authorize_redirect(request, redirect_uri=redirect, scope='identify email guilds guilds.members.read')


@app.route('/oauth')
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

    return RedirectResponse(request.url_for('admin:admin_index'))


@app.route('/logout')
async def admin_logout(request: Request):
    del request.session['discord']
    del request.session['user']
    return templates.TemplateResponse('message.html', {'request': request, 'header': 'wylogowano'})


@app.route('/')
@requires('authenticated')
async def admin_index(request: Request):
    async with RESTApp().acquire(request.session['discord']['access_token']) as client:
        # awaiting = VerificationRequest.objects()
        awaiting = []
        return templates.TemplateResponse('admin/base.html', {'request': request, 'awaiting': awaiting})
