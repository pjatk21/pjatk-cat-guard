import os
from datetime import datetime

from google.oauth2 import id_token
from google.auth.transport import requests

import random_word
from aiohttp import ClientSession
from dotenv import load_dotenv
from hikari import RESTApp
from pymongo import MongoClient
from bson import ObjectId
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response, PlainTextResponse
from starlette.routing import Route
from starlette.exceptions import HTTPException
from starlette.templating import Jinja2Templates
from discordcat.embed_factory import embed_success

from common.codes import VerificationCode

load_dotenv()

env = os.environ


mongo = MongoClient(env.get("MONGODB_URL"))
db = mongo["catguard"]
codes = db["codes"]
verified = db["verified"]
rest = RESTApp()
templates = Jinja2Templates(directory="templates")


class InviteEndpoint(HTTPEndpoint):
    async def get(self, request: Request):
        return templates.TemplateResponse(
            "home.html", {"request": request, "invitation": env.get("INVITATION")}
        )


class ExceptionsPreviewer(HTTPEndpoint):
    async def get(self, request: Request):
        exception = db["exceptions"].find_one(
            {"_id": ObjectId(request.path_params["_id"])}
        )

        if exception is None:
            raise HTTPException(status_code=404)

        return templates.TemplateResponse(
            "report.html", {"request": request, "exception": exception}
        )


class LoginGate(HTTPEndpoint):
    async def get(self, request: Request):
        secret = request.path_params["secret"]
        return templates.TemplateResponse(
            "oauth-login.html",
            {
                "request": request,
                "secret": secret,
                "redirect": f"{env.get('VERIFICATION_URL')}login",
            },
        )

    async def post(self, request: Request):
        form = await request.form()
        secret = form["state"]
        credential = form["credential"]
        link_data = db["link"].find_one({"secret": secret})

        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                requests.Request(),
                "415405805208-n7irpdbl5go8cs5jf15i8005gd53iume.apps.googleusercontent.com",
            )
            assert idinfo.get("sub") is not None
        except ValueError:
            # Invalid token
            return PlainTextResponse("Fuck you", status_code=400)

        previous_verification = verified.find_one(
            {
                "$or": [
                    {"discord_id": link_data["discord_id"]},
                    {"student_mail": idinfo["email"]},
                ]
            }
        )

        if previous_verification is not None:
            return PlainTextResponse(
                f"Te dane już są połączone z {previous_verification}"
            )

        async with rest.acquire(env.get("DISCORD_TOKEN"), "Bot") as client:
            user = await client.fetch_user(link_data["discord_id"])
            when = datetime.now()

            verfied_role = db["roles"].find_one({"guild_id": link_data["guild_id"]})
            await client.add_role_to_member(
                link_data["guild_id"], link_data["discord_id"], verfied_role["role_id"]
            )

            verified.insert_one(
                {
                    "student_mail": idinfo["email"],
                    "discord_id": user.id,
                    "when": when,
                    "guild_id": link_data["guild_id"],
                    "verified_by": "oauth-verified",
                    "oauth": idinfo | {"credential": credential},
                }
            )

            embed = embed_success(
                "Pomyślnie zweryfikowano! Możesz zarządzać weryfikacją poprzez komendę `/manage self`"
            )
            embed.add_field(
                "Serwer", str(await client.fetch_guild(link_data["guild_id"]))
            )
            embed.add_field("Data weryfikacji", when.isoformat())
            embed.add_field("Powiązany email", idinfo["email"])
            embed.add_field("Metoda weryfikacji", "OAuth")

            await user.send(embed=embed)

            db["link"].delete_many({"discord_id": user.id})

        return templates.TemplateResponse("verified.html", {"request": request})


routes = [
    Route("/", InviteEndpoint),
    Route("/oauth/{secret}", LoginGate),
    Route("/login", LoginGate),
    Route("/exceptions/{_id}", ExceptionsPreviewer),
]
app = Starlette(routes=routes)
