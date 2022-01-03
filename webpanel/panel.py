from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.routing import Route

from shared.db import init_connection
from .endpoints.invites import LoginGate, GuildInviteEndpoint
from .endpoints.general import AboutPage

load_dotenv()
init_connection()


routes = [
    Route("/", AboutPage),
    Route("/oauth/{secret}", LoginGate),
    Route("/login", LoginGate),
    Route("/join/pjatk2021", GuildInviteEndpoint),
]
app = Starlette(routes=routes)
