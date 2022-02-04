from dotenv import load_dotenv
from google.auth.transport import requests
from google.oauth2 import id_token
from mongoengine import Q
from starlette.applications import Starlette
from starlette.datastructures import UploadFile
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse

from shared.db import init_connection
from shared.documents import VerificationRequest, VerificationPhoto, VerificationGoogle, TrustedUser, VerificationState
from webpanel.common import templates
from mongoengine.errors import DoesNotExist

load_dotenv()
init_connection()

app = Starlette()


@app.route('/oauth', methods=['POST'])
async def google_oauth(request: Request):
    form = await request.form()
    secret = form["state"]
    credential = form["credential"]

    try:
        vr: VerificationRequest = VerificationRequest.objects(code=secret).get()
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

    return RedirectResponse(request.url_for('verify:form', secret=secret))


@app.route('/{secret}', name='form')
class LoginQueueRequest(HTTPEndpoint):
    async def get(self, request: Request):
        secret = request.path_params["secret"]

        try:
            vr: VerificationRequest = VerificationRequest.objects(code=secret).get()
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
            vr: VerificationRequest = VerificationRequest.objects(code=secret).get()
        except DoesNotExist:
            raise HTTPException(404)

        if vr.photo_front and vr.photo_back and vr.google:
            vr.state = VerificationState.IN_REVIEW
            vr.save()
            return RedirectResponse(request.url_for('verify:form', secret=secret), status_code=302)

        form = await request.form()
        if form.get('photo-front'):
            pf: UploadFile = form['photo-front']
            if pf.content_type != 'application/octet-stream':
                vr.photo_front = VerificationPhoto(
                    photo=pf.file.read(),
                    content_type=pf.content_type,
                    content_name=pf.filename
                )

        if form.get('photo-back'):
            pf: UploadFile = form['photo-back']
            if pf.content_type != 'application/octet-stream':
                vr.photo_back = VerificationPhoto(
                    photo=pf.file.read(),
                    content_type=pf.content_type,
                    content_name=pf.filename
                )

        vr.save()

        return RedirectResponse(request.url_for('verify:form', secret=secret), status_code=302)
