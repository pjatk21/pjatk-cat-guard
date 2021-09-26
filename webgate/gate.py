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

        async with ClientSession(
            headers={
                "Authorization": "Bearer a87bc15a4e3fd1",
                "Accept": "application/json",
            }
        ) as client:
            async with client.get(
                f"https://ipinfo.io/{request.client.host}"
            ) as response:
                about_ip = await response.json()

        async with rest.acquire(env.get("DISCORD_TOKEN"), "Bot") as client:
            user = await client.fetch_user(trusted_code.user_id)

            verified.insert_one(
                {
                    "student_mail": trusted_code.email,
                    "discord_id": user.id,
                    "when": datetime.now(),
                    "about-ip": about_ip,
                }
            )

            verfied_role = db["roles"].find_one({"guild_id": trusted_code.target_guild})
            await client.add_role_to_member(
                trusted_code.target_guild, trusted_code.user_id, verfied_role["role_id"]
            )
            await user.send(
                f"Zweryfikowano na serwerze {(await client.fetch_guild(trusted_code.target_guild)).name}"
                f" i dodano rangę dla zweryfikowanych użytkowników!"
            )

        codes.delete_many({"who": trusted_code.who})
        codes.delete_many({"email": trusted_code.email})

        return templates.TemplateResponse("verified.html", {"request": request})


routes = [
    Route("/", InviteEndpoint),
    Route("/verify/{code}", VerificationGate),
]
app = Starlette(routes=routes)
