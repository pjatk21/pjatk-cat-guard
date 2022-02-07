import re
from datetime import datetime

from dotenv import load_dotenv
from google.auth.transport import requests
from google.oauth2 import id_token
from mongoengine.errors import DoesNotExist, NotUniqueError
from starlette.applications import Starlette
from starlette.background import BackgroundTasks
from starlette.datastructures import UploadFile
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

import webpanel.tasks
from shared.consts import data_path
from shared.db import init_connection
from shared.documents import VerificationRequest, VerificationGoogle, TrustedUser, VerificationState, \
    GuildConfiguration, VerificationMethod
from webpanel.common import templates, save_picture

load_dotenv()
init_connection()

app = Starlette()


@app.route('/oauth', methods=['POST'])
async def google_oauth(request: Request):
    form = await request.form()
    secret = form["state"]
    credential = form["credential"]

    try:
        vr: VerificationRequest = VerificationRequest.objects.get(code=secret)
    except DoesNotExist:
        raise HTTPException(404)

    if vr.trust:
        raise HTTPException(400)

    try:
        id_info = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            "415405805208-n7irpdbl5go8cs5jf15i8005gd53iume.apps.googleusercontent.com",
        )
        assert id_info.get("sub") is not None
    except ValueError:
        raise HTTPException(400)

    google_data = VerificationGoogle(
        email=id_info['email'],
        name=id_info['name'],
        raw=id_info,
    )

    mismatches_mail = VerificationRequest.objects(
        google__email=google_data.email, trust__ne=None
    )
    mismatches_discord = TrustedUser.objects(
        identity=vr.identity
    )

    if len(mismatches_mail) + len(mismatches_discord):
        return templates.TemplateResponse(
            "message.html", {
                'request': request,
                'header': 'Poniższe dane, już są w bazie danych',
                'message': 'Jeżeli nie rejestrowałeś konta wcześniej, skontaktuj się z administracją.'
            }
        )

    vr.google = google_data
    vr.save()

    if re.match(r'ARB-\w{8}-\w{3}', vr.code):
        return await bypassed(request, vr)

    return RedirectResponse(request.url_for('verify:form', secret=secret))


async def bypassed(request: Request, vr: VerificationRequest):
    conf: GuildConfiguration = GuildConfiguration.objects.get(guild_id=vr.identity.guild_id)

    trust = TrustedUser()
    trust.identity = vr.identity
    trust.student_number = vr.no
    trust.verification_method = VerificationMethod.REVIEW

    try:
        trust.save()
    except NotUniqueError:
        vr.delete()
        return RedirectResponse(request.url_for('verify:form', secret=vr.code))

    vr.trust = trust
    vr.update_state(VerificationState.ACCEPTED, vr.reviewer)
    vr.accepted = datetime.now().astimezone()
    vr.save()

    tasks = BackgroundTasks()
    tasks.add_task(webpanel.tasks.apply_trusted_role, trust, conf)
    tasks.add_task(webpanel.tasks.send_trust_confirmation, vr)
    tasks.add_task(webpanel.tasks.remove_duplicate_requests, vr)

    return RedirectResponse(request.url_for('verify:form', secret=vr.code), background=tasks, status_code=302)


@app.route('/{secret}', name='form')
class LoginQueueRequest(HTTPEndpoint):
    async def get(self, request: Request):
        secret = request.path_params["secret"]

        try:
            vr: VerificationRequest = VerificationRequest.objects.get(code=secret)
        except DoesNotExist:
            raise HTTPException(404)

        return templates.TemplateResponse(
            'upload.html',
            {'request': request, 'vr': vr, 'secret': vr.code,
             'redirect': request.url_for('verify:google_oauth')}
        )

    async def post(self, request: Request):
        secret = request.path_params["secret"]

        try:
            vr: VerificationRequest = VerificationRequest.objects.get(code=secret)
        except DoesNotExist:
            raise HTTPException(404)

        if vr.state == VerificationState.ID_REQUIRED:
            form = await request.form()

            if form.get('photo-front'):
                pf: UploadFile = form['photo-front']
                if pf.content_type != 'application/octet-stream':
                    vr.photos.front = save_picture(vr, pf, 'front')

            if form.get('photo-back'):
                pf: UploadFile = form['photo-back']
                if pf.content_type != 'application/octet-stream':
                    vr.photos.back = save_picture(vr, pf, 'back')

        tasks = BackgroundTasks()

        if vr.state == VerificationState.ID_REQUIRED and vr.photos.ready:
            tasks.add_task(webpanel.tasks.notify_reviewer_docs, vr, request)

        if vr.google and vr.state == VerificationState.PENDING:
            vr.state = VerificationState.IN_REVIEW
            tasks.add_task(webpanel.tasks.notify_reviewers, vr, request)

        vr.save()

        return RedirectResponse(request.url_for('verify:form', secret=secret), status_code=302, background=tasks)
