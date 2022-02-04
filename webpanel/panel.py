import logging
import os

from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

import webpanel.admin
import webpanel.verify
from shared.db import init_connection
from .endpoints import invites, general

load_dotenv()
init_connection()


routes = [
    Route("/", general.AboutPage),
    # Route("/verify/{secret}", invites.LoginQueueRequest),
    # Route("/verify/google", invites.LoginQueueRequest),
    Route("/join/pjatk2021", invites.GuildInviteEndpoint),
    Mount("/static", app=StaticFiles(directory='webpanel/static'), name="static"),
    Mount("/admin", app=webpanel.admin.app, name='admin'),
    Mount("/verify", app=webpanel.verify.app, name='verify')
]

if not os.getenv('COOKIE_SECRET'):
    logging.warning('Cookie secret hasn\'t been passed')

app = Starlette(routes=routes)
