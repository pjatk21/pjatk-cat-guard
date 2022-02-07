import asyncio
import logging
import os
import re
import uuid
from datetime import timedelta, datetime

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from hikari import RESTApp
from mongoengine import DoesNotExist, Q, NotUniqueError
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.background import BackgroundTasks
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, FileResponse

import webpanel.tasks
from shared.db import init_connection
from shared.documents import VerificationRequest, GuildConfiguration, VerificationState, TrustedUser, \
    VerificationMethod, Reviewer, VerificationRejection, UserIdentity
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
    Middleware(SessionMiddleware, secret_key=os.getenv('COOKIE_SECRET', 'someoneforgotcookiesecretrecipe'),
               max_age=timedelta(hours=6).seconds),
    Middleware(AuthenticationMiddleware, backend=DiscordAuthBackend())
]

app = Starlette(middleware=middleware)


@app.exception_handler(403)
async def admin_forbidden(req: Request, exc):
    req.session['login_redirect'] = str(req.url)
    return templates.TemplateResponse('admin/403.html', {'request': req}, status_code=403)


@app.exception_handler(404)
async def admin_forbidden(req, exc):
    return templates.TemplateResponse('admin/404.html', {'request': req}, status_code=404)


@app.exception_handler(500)
async def admin_forbidden(req, exc):
    return templates.TemplateResponse('admin/500.html', {'request': req, 'exc': exc}, status_code=500)


@app.route('/login')
async def admin_login(request: Request):
    ds = oauth_discord.create_client('discord')
    redirect = request.url_for('admin:admin_oauth')
    return await ds.authorize_redirect(request, redirect_uri=redirect,
                                       scope='identify email guilds guilds.members.read')


@app.route('/oauth')
async def admin_oauth(request: Request):
    ds = oauth_discord.create_client('discord')
    token = await ds.authorize_access_token(request)
    async with RESTApp().acquire(token['access_token']) as client:
        user = await client.fetch_my_user()

        try:
            rev = Reviewer.objects.get(identity__user_id=user.id)
        except DoesNotExist:
            return templates.TemplateResponse('message.html',
                                              {'request': request, 'header': 'Nie jesteś wyznaczony na sprawdzającego.',
                                               'paragraphs': ['sorka']})

        request.session['discord'] = token
        request.session['user'] = str(user)
        request.session['discord']['id'] = user.id
        request.session['reviewer'] = str(rev.id)

    if request.session.get('login_redirect'):
        lr = request.session.pop('login_redirect')
        return RedirectResponse(lr, status_code=302)

    return RedirectResponse(request.url_for('admin:admin_index'))


@app.route('/logout')
async def admin_logout(request: Request):
    request.session.clear()
    return templates.TemplateResponse('message.html', {'request': request, 'header': 'wylogowano'})


@app.route('/')
@requires('authenticated')
async def admin_index(request: Request):
    stats = {}
    bypass_guilds = []

    async with RESTApp().acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as bot:
        for gc in GuildConfiguration.objects():
            members, guild = await asyncio.gather(bot.fetch_members(gc.guild_id), bot.fetch_guild(gc.guild_id))
            tr_count = len([mem for mem in members if gc.trusted_role_id in mem.role_ids])
            stats |= {guild: f'{100 * tr_count / len(members):.2f}%'}
            bypass_guilds.append({'id': guild.id, 'name': str(guild)})

    awaiting = VerificationRequest.objects(
        Q(state=VerificationState.IN_REVIEW) | Q(state=VerificationState.ID_REQUIRED)).order_by('-submitted')
    return templates.TemplateResponse('admin/base.html', {'request': request, 'awaiting': awaiting, 'stats': stats,
                                                          'bypass': bypass_guilds})


@app.route('/bypass/', methods=['POST'])
async def admin_bypass(request: Request):
    form = await request.form()
    rev: Reviewer = Reviewer.objects.get(id=request.session['reviewer'])

    async with RESTApp().acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as bot:
        member = await bot.fetch_member(form['guild'], form['user'])
        identity = UserIdentity()
        identity.user_id = member.id
        identity.guild_id = member.guild_id
        identity.user_name = str(member)
        identity.guild_name = str(await bot.fetch_guild(member.guild_id))

    email = f'{form["student_no"]}@pjwstk.edu.pl'

    vr = VerificationRequest()
    vr.identity = identity
    vr.reviewer = rev
    vr.code = f'ARB-{str(uuid.uuid4())[:12]}'
    vr.update_state(VerificationState.BYPASSED, rev)
    vr.save()

    tasks = BackgroundTasks()
    tasks.add_task(webpanel.tasks.notify_bypass_email, email, vr, request)

    return RedirectResponse(request.url_for('admin:admin_index'), status_code=302, background=tasks)


@app.route('/accepted', name='accepted')
@requires('authenticated')
async def admin_accepted(request: Request):
    query = Q(state=VerificationState.ACCEPTED)
    if request.query_params.get('search'):
        s = request.query_params['search']
        query &= Q(google__email__icontains=s) | Q(identity__user_name__icontains=s)

    accepted = VerificationRequest.objects(query).order_by('-accepted')
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
        rejected = VerificationRequest.objects(state=VerificationState.REJECTED).order_by('-rejection__when')
    return templates.TemplateResponse('admin/rejected.html', {'request': request, 'rejected': rejected})


@app.route('/review/{rid}', name='review')
class AdminReview(HTTPEndpoint):
    @requires('authenticated')
    async def get(self, request: Request):
        try:
            vr: VerificationRequest = VerificationRequest.objects.get(id=request.path_params['rid'])
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
            vr: VerificationRequest = VerificationRequest.objects.get(id=request.path_params['rid'])
            conf: GuildConfiguration = GuildConfiguration.objects.get(guild_id=vr.identity.guild_id)
            rev: Reviewer = Reviewer.objects.get(id=request.session['reviewer'])
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
        vr.update_state(VerificationState.ACCEPTED, rev)
        vr.reviewer = rev
        vr.accepted = datetime.now().astimezone()
        vr.save()

        tasks = BackgroundTasks()
        tasks.add_task(webpanel.tasks.apply_trusted_role, trust, conf)
        tasks.add_task(webpanel.tasks.send_trust_confirmation, vr)
        tasks.add_task(webpanel.tasks.remove_duplicate_requests, vr)

        return RedirectResponse(request.url_for('admin:review', rid=vr.id), background=tasks, status_code=302)


@app.route('/confirm-id/{rid}', name='id required', methods=['POST'])
@requires('authenticated')
async def admin_id_req(request: Request):
    try:
        vr: VerificationRequest = VerificationRequest.objects.get(id=request.path_params['rid'])
        rev: Reviewer = Reviewer.objects.get(id=request.session['reviewer'])
    except DoesNotExist:
        raise HTTPException(404)

    tasks = BackgroundTasks()

    vr.update_state(VerificationState.ID_REQUIRED, rev)
    vr.reviewer = rev

    if vr.trust:
        vr.remove_trust()
        tasks.add_task(webpanel.tasks.removed_trusted_role, vr)

    vr.save()
    tasks.add_task(webpanel.tasks.notify_requested_id, vr, request)
    tasks.add_task(webpanel.tasks.notify_requested_id_mail, vr, request)
    tasks.add_task(webpanel.tasks.remove_duplicate_requests, vr)

    return RedirectResponse(request.url_for('admin:review', rid=vr.id), status_code=302, background=tasks)


@app.route('/reject/{rid}', name='reject', methods=['POST'])
@requires('authenticated')
async def admin_reject(request: Request):
    form = await request.form()

    try:
        vr: VerificationRequest = VerificationRequest.objects.get(id=request.path_params['rid'])
        rev: Reviewer = Reviewer.objects.get(id=request.session['reviewer'])
    except DoesNotExist:
        raise HTTPException(404)

    vr.update_state(VerificationState.REJECTED, rev)
    vr.rejection = VerificationRejection(reason=form['reason'])
    vr.reviewer = rev
    vr.save()

    tasks = BackgroundTasks()

    if vr.trust:
        vr.remove_trust()
        tasks.add_task(webpanel.tasks.removed_trusted_role, vr)

    tasks.add_task(webpanel.tasks.send_rejection_mail, vr, form['reason'])
    tasks.add_task(webpanel.tasks.send_rejection_dm, vr, form['reason'])
    tasks.add_task(webpanel.tasks.remove_duplicate_requests, vr)

    return RedirectResponse(request.url_for('admin:admin_index'), status_code=302, background=tasks)


@app.route('/photoproxy/{rid}/{side}.jpg', name='photoproxy', methods=['GET'])
@requires('authenticated')
async def photo_proxy(request: Request):
    side = request.path_params['side']
    rid = request.path_params['rid']

    try:
        vr: VerificationRequest = VerificationRequest.objects.get(id=rid)
    except DoesNotExist:
        raise HTTPException(404)

    if not vr.photos.ready:
        raise HTTPException(404)

    match side:
        case 'front':
            logging.info('photoproxy front %s -> %s', str(vr.id), vr.photos.front)
            return FileResponse(vr.photos.front)
        case 'back':
            logging.info('photoproxy back %s -> %s', str(vr.id), vr.photos.back)
            return FileResponse(vr.photos.back)
        case _:
            raise HTTPException(400)
