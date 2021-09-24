import os

from dotenv import load_dotenv
from hikari import RESTApp
from pymongo import MongoClient
from starlette.applications import Starlette
from starlette.responses import RedirectResponse, PlainTextResponse
from starlette.routing import Route
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from common.codes import VerificationCode

load_dotenv()

env = os.environ


mongo = MongoClient(env.get("MONGODB_URL"))
db = mongo["verifications"]
codes = db["codes"]
registered = db["registered"]
rest = RESTApp()


class VerificationGate(HTTPEndpoint):
    async def get(self, request: Request):
        code = request.path_params["code"]

        trusted_code = codes.find_one({"code": code})

        if trusted_code is None:
            return RedirectResponse(env.get('FAIL_REDIRECT'))

        del trusted_code["_id"]
        trusted_code = VerificationCode(**trusted_code)

        if trusted_code.has_expired:
            return RedirectResponse(env.get('FAIL_REDIRECT'))

        codes.delete_many({"who": trusted_code.who})
        codes.delete_many({"email": trusted_code.email})

        async with rest.acquire(
            env.get("DISCORD_TOKEN"), "Bot"
        ) as client:
            user = await client.fetch_user(trusted_code.user_id)
            await user.send("Zweryfikowano i dodano rangę!")

            registered.insert_one({"student_id": trusted_code.who, "discord_id": user.id})

        return PlainTextResponse("ok")


routes = [Route("/{code}", VerificationGate)]
app = Starlette(routes=routes)
