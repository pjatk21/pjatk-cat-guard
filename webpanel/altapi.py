import httpx
from mongoengine import DoesNotExist
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request

from shared.documents import AltapiConfiguration
from webpanel.common import templates

app = Starlette()


@app.route('/configure/{id}', methods=['GET'])
async def altapi_config(request: Request):
    try:
        ac: AltapiConfiguration = AltapiConfiguration.objects.get(id=request.path_params.get('id'))
    except DoesNotExist:
        raise HTTPException(404)

    # TODO: change to async
    groups = httpx.get('https://altapi.kpostek.dev/v1/timetable/groups').json()

    return templates.TemplateResponse('altapi-conf.html', {'request': request, 'groups': sorted(groups['groupsAvailable']), 'gset': ac.groups })
