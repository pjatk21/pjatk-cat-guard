import logging
import os

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from webpanel.common import templates
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from hikari import RESTApp

from shared.db import init_connection
from shared.documents import GuildConfiguration
from .endpoints import invites, general, mailing

load_dotenv()
init_connection()


oauth_discord = OAuth()
oauth_discord.register(
    'discord',
    client_id=890520093660971058,
    client_secret='dXyuGXJrkFIP-Lu_wCLMX-qOloqPr2oJ',
    authorize_url="https://discord.com/api/oauth2/authorize",
    token_endpoint="https://discord.com/api/oauth2/token",
    client_kwargs={'scope': 'identify email guilds connections'}
)

routes = [
    Route("/", general.AboutPage),
    Route("/oauth/{secret}", invites.LoginGate),
    Route("/login", invites.LoginGate),
    Route("/join/pjatk2021", invites.GuildInviteEndpoint),
    # Mount("/admin", routes=admin.routes),
    Mount("/mail", routes=mailing.routes),
    Mount("/static", app=StaticFiles(directory='webpanel/static'), name="static")
]

middleware = [
    Middleware(SessionMiddleware, secret_key=os.getenv('COOKIE_SECRET', 'someoneforgotcookiesecretrecipe'))
]

if not os.getenv('COOKIE_SECRET'):
    logging.warning('Cookie secret hasn\'t been passed')

app = Starlette(routes=routes, middleware=middleware)


@app.route('/admin/login')
async def admin_login(request: Request):
    ds = oauth_discord.create_client('discord')
    redirect = request.url_for('admin_oauth')
    return await ds.authorize_redirect(request, redirect_uri=redirect)


@app.route('/admin/oauth')
async def admin_oauth(request: Request):
    ds = oauth_discord.create_client('discord')
    token = await ds.authorize_access_token(request)
    async with RESTApp().acquire(token['access_token']) as client:
        user = await client.fetch_my_user()

        request.session['discord'] = token
        request.session['user'] = str(user)

    return RedirectResponse(request.url_for('admin_index'))


@app.route('/admin/')
async def admin_index(request: Request):
    async with RESTApp().acquire(request.session['discord']['access_token']) as client:
        return JSONResponse(
            {
                'msg': f'hi {request.session["user"]}',
                'guilds': [str(g) for g in await client.fetch_my_guilds()],
            }
        )


@app.route('/gate')
async def verify_gate(request: Request):
    return templates.TemplateResponse('upload.html', {"request": request})
