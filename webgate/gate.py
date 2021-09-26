import os
from datetime import datetime

from aiohttp import ClientSession
from dotenv import load_dotenv
from hikari import RESTApp
from pymongo import MongoClient
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route
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


class VerificationGate(HTTPEndpoint):
    async def get(self, request: Request):
        code = request.path_params["code"]

        trusted_code = codes.find_one({"code": code})

        if trusted_code is None:
            return RedirectResponse(env.get("FAIL_REDIRECT"))

        del trusted_code["_id"]
        trusted_code = VerificationCode(**trusted_code)

        if trusted_code.has_expired:
            return RedirectResponse(env.get("FAIL_REDIRECT"))

        async with rest.acquire(env.get("DISCORD_TOKEN"), "Bot") as client:
            user = await client.fetch_user(trusted_code.user_id)
            when = datetime.now()
            verified.insert_one(
                {
                    "student_mail": trusted_code.email,
                    "discord_id": user.id,
                    "when": when,
                }
            )

            verfied_role = db["roles"].find_one({"guild_id": trusted_code.target_guild})
            await client.add_role_to_member(
                trusted_code.target_guild, trusted_code.user_id, verfied_role["role_id"]
            )

            embed = embed_success("Pomyślnie zweryfikowano! Możesz zarządzać weryfikacją poprzez komendę /manage")
            embed.add_field("Serwer weryfikukący", str(await client.fetch_guild(trusted_code.target_guild)))
            embed.add_field("Data weryfikacji", when.isoformat())
            embed.add_field("Powiązany email", trusted_code.email)

            await user.send(embed=embed)

        codes.delete_many({"who": trusted_code.who})
        codes.delete_many({"email": trusted_code.email})

        return templates.TemplateResponse("verified.html", {"request": request})


routes = [
    Route("/", InviteEndpoint),
    Route("/verify/{code}", VerificationGate),
]
app = Starlette(routes=routes)
