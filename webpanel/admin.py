import os
import re
from datetime import timedelta

from authlib.integrations.starlette_client import OAuth
from bson import ObjectId
from dotenv import load_dotenv
from hikari import RESTApp
from mongoengine import DoesNotExist, Q, NotUniqueError
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
from shared.documents import VerificationRequest, GuildConfiguration, VerificationState, TrustedUser, \
    VerificationMethod, Reviewer, VerificationRejection
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
    Middleware(SessionMiddleware, secret_key=os.getenv('COOKIE_SECRET', 'someoneforgotcookiesecretrecipe'), max_age=timedelta(hours=6).seconds),
    Middleware(AuthenticationMiddleware, backend=DiscordAuthBackend())
]

app = Starlette(middleware=middleware)


@app.exception_handler(403)
async def admin_forbidden(req, exc):
    return templates.TemplateResponse('admin/403.html', {'request': req})


@app.exception_handler(404)
async def admin_forbidden(req, exc):
    return templates.TemplateResponse('admin/404.html', {'request': req})


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

        try:
            rev = Reviewer.objects(identity__user_id=user.id).get()
        except DoesNotExist:
            return templates.TemplateResponse('message.html', {'request': request, 'header': 'Nie jesteś wyznaczony na sprawdzającego.', 'paragraphs': ['sorka']})

        request.session['discord'] = token
        request.session['user'] = str(user)
        request.session['discord']['id'] = user.id
        request.session['reviewer'] = str(rev.id)

    return RedirectResponse(request.url_for('admin:admin_index'))


@app.route('/logout')
async def admin_logout(request: Request):
    request.session.clear()
    return templates.TemplateResponse('message.html', {'request': request, 'header': 'wylogowano'})


@app.route('/')
@requires('authenticated')
async def admin_index(request: Request):
    awaiting = VerificationRequest.objects(Q(state=VerificationState.IN_REVIEW) | Q(state=VerificationState.ID_REQUIRED)).order_by('-submitted')
    return templates.TemplateResponse('admin/base.html', {'request': request, 'awaiting': awaiting})


@app.route('/accepted', name='accepted')
@requires('authenticated')
async def admin_accepted(request: Request):
    query = Q(state=VerificationState.ACCEPTED)
    if request.query_params.get('search'):
        s = request.query_params['search']
        query &= Q(google__email__icontains=s) | Q(identity__user_name__icontains=s)

    accepted = VerificationRequest.objects(query).order_by('-submitted')
    return templates.TemplateResponse('admin/accepted.html', {'request': request, 'accepted': accepted})


@app.route('/rejected', name='rejected')
@requires('authenticated')
async def admin_rejected(request: Request):
    if request.query_params.get('search'):
        s = request.query_params['search']
        rejected = VerificationRequest.objects(
            Q(state=VerificationState.REJECTED) & Q(rejection__reason__icontains=s) | Q(google__email__icontains=s)
        ).order_by('-submitted')
    else:
        rejected = VerificationRequest.objects(state=VerificationState.REJECTED).order_by('-submitted')
    return templates.TemplateResponse('admin/rejected.html', {'request': request, 'rejected': rejected})


@app.route('/review/{rid}', name='review')
class AdminReview(HTTPEndpoint):
    @requires('authenticated')
    async def get(self, request: Request):
        try:
            vr: VerificationRequest = VerificationRequest.objects(id=request.path_params['rid']).get()
        except DoesNotExist:
            raise HTTPException(404)

        warns = {}

        async with RESTApp().acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as bot:
            user = await bot.fetch_member(vr.identity.guild_id, vr.identity.user_id)

        warns['fresh_meat'] = (user.joined_at - user.created_at).days < 365
        warns['weird_num'] = not re.match(r'^s2[456]\d{3}$', vr.no)

        return templates.TemplateResponse(
            'admin/review.html',
            {'request': request, 'vr': vr, 'ds': user, 'warns': warns}
        )

    @requires('authenticated')
    async def post(self, request: Request):
        try:
            vr: VerificationRequest = VerificationRequest.objects(id=request.path_params['rid']).get()
            conf: GuildConfiguration = GuildConfiguration.objects(guild_id=vr.identity.guild_id).get()
        except DoesNotExist:
            raise HTTPException(404)

        trust = TrustedUser()
        trust.identity = vr.identity
        trust.student_number = vr.no
        trust.verification_method = VerificationMethod.REVIEW

        try:
            trust.save()
        except NotUniqueError:
            vr.delete()
            return templates.TemplateResponse('admin/autodelete.html', {'request': request})

        vr.trust = trust
        vr.state = VerificationState.ACCEPTED
        vr.reviewer = ObjectId(request.session['reviewer'])
        vr.save()
        VerificationRequest.objects(identity=vr.identity, id__ne=vr.id, state=VerificationState.PENDING).delete()

        tasks = BackgroundTasks()
        tasks.add_task(webpanel.tasks.apply_trusted_role, trust, conf)
        tasks.add_task(webpanel.tasks.send_trust_confirmation, vr)

        return RedirectResponse(request.url_for('admin:review', rid=vr.id), background=tasks, status_code=302)


@app.route('/id-req/{rid}', name='id required', methods=['POST'])
@requires('authenticated')
async def admin_id_req(request: Request):
    try:
        vr: VerificationRequest = VerificationRequest.objects(id=request.path_params['rid']).get()
    except DoesNotExist:
        raise HTTPException(404)

    tasks = BackgroundTasks()

    vr.state = VerificationState.ID_REQUIRED
    vr.reviewer = ObjectId(request.session['reviewer'])

    if vr.trust:
        trust = vr.trust
        vr.trust = None
        vr.save()
        trust.delete()
        tasks.add_task(webpanel.tasks.removed_trusted_role, vr)

    vr.save()
    tasks.add_task(webpanel.tasks.notify_requested_id, vr)

    return RedirectResponse(request.url_for('admin:review', rid=vr.id), status_code=302, background=tasks)


@app.route('/reject/{rid}', name='reject', methods=['POST'])
@requires('authenticated')
async def admin_reject(request: Request):
    form = await request.form()

    try:
        vr: VerificationRequest = VerificationRequest.objects(id=request.path_params['rid']).get()
    except DoesNotExist:
        raise HTTPException(404)

    vr.state = VerificationState.REJECTED
    vr.rejection = VerificationRejection(reason=form['reason'])
    vr.reviewer = ObjectId(request.session['reviewer'])
    vr.save()

    tasks = BackgroundTasks()
    tasks.add_task(webpanel.tasks.send_rejection_mail, vr, form['reason'])
    tasks.add_task(webpanel.tasks.send_rejection_dm, vr, form['reason'])

    return RedirectResponse(request.url_for('admin:admin_index'), status_code=302, background=tasks)


@app.route('/photoproxy/{side}-{rid}.jpg', name='photoproxy')
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
