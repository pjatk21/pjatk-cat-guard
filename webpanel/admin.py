import os
import re

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from hikari import RESTApp
from mongoengine import DoesNotExist
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from shared.db import init_connection
from shared.documents import VerificationRequest, GuildConfiguration, VerificationState, TrustedUser, VerificationMethod
from webpanel.common import templates
from webpanel.middleware.auth import DiscordAuthBackend
import webpanel.tasks

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
    awaiting = VerificationRequest.objects(state=VerificationState.IN_REVIEW)
    return templates.TemplateResponse('admin/base.html', {'request': request, 'awaiting': awaiting})


@app.route('/review/{rid}', name='review')
class AdminReview(HTTPEndpoint):
    @requires('authenticated')
    async def get(self, request: Request):
        try:
            vr: VerificationRequest = VerificationRequest.objects(id=request.path_params['rid']).get()
        except DoesNotExist:
            raise HTTPException(404)

        return templates.TemplateResponse('admin/review.html', {'request': request, 'vr': vr})

    @requires('authenticated')
    async def post(self, request: Request):
        try:
            vr: VerificationRequest = VerificationRequest.objects(id=request.path_params['rid']).get()
            conf: GuildConfiguration = GuildConfiguration.objects(guild_id=vr.identity.guild_id).get()
        except DoesNotExist:
            raise HTTPException(404)

        trust = TrustedUser()
        trust.identity = vr.identity
        trust.student_number = re.search(r's\d+', vr.google.email).string
        trust.verification_method = VerificationMethod.REVIEW
        trust.save()

        vr.trust = trust
        vr.state = VerificationState.ACCEPTED
        vr.save()

        tasks = BackgroundTasks()
        tasks.add_task(webpanel.tasks.apply_trusted_role, trust, conf)
        tasks.add_task(webpanel.tasks.send_trust_confirmation, vr)

        return RedirectResponse(request.url_for('admin:admin_index'), background=tasks, status_code=302)


@app.route('/reject/{rid}', name='reject', methods=['POST'])
@requires('authenticated')
async def admin_reject(request: Request):
    form = await request.form()

    try:
        vr: VerificationRequest = VerificationRequest.objects(id=request.path_params['rid']).get()
    except DoesNotExist:
        raise HTTPException(404)

    tasks = BackgroundTasks()
    tasks.add_task(webpanel.tasks.send_rejection_mail, vr, form['reason'])
    tasks.add_task(webpanel.tasks.send_rejection_dm, vr, form['reason'])

    vr.state = VerificationState.REJECTED
    vr.save()
    return RedirectResponse(request.url_for('admin:admin_index'), status_code=302, background=tasks)


@app.route('/photoproxy/{side}-{rid}', name='photoproxy')
class PhotoProxy(HTTPEndpoint):
    @requires('authenticated')
    async def get(self, request: Request):
        side = request.path_params['side']
        rid = request.path_params['rid']

        try:
            vr: VerificationRequest = VerificationRequest.objects(id=rid).get()
        except DoesNotExist:
            raise HTTPException(404)

        match side:
            case 'front':
                return Response(content=vr.photo_front.photo, media_type=vr.photo_front.content_type)
            case 'back':
                return Response(content=vr.photo_back.photo, media_type=vr.photo_back.content_type)
            case _:
                raise HTTPException(400)
