import os
from datetime import timedelta
from starlette.exceptions import HTTPException

from hikari import RESTApp
from httpx import AsyncClient
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request

from webpanel.common import templates


async def gen_guild_invite(channel_id: int):
    async with RESTApp().acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
        return await bot.create_invite(
            channel_id, max_uses=1, max_age=timedelta(minutes=5), reason="Automated invite generator"
        )


class GuildInviteEndpoint(HTTPEndpoint):
    def get(self, request: Request):
        return templates.TemplateResponse("guild-invite.html", {"request": request})

    async def post(self, request: Request):
        ac = AsyncClient()
        response = await ac.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": os.getenv("RECAPTCHA_SECRET"),
                "response": (await request.form()).get("g-recaptcha-response"),
            }
        )

        if not response.json()["success"]:
            raise HTTPException(400)

        return templates.TemplateResponse(
            "guild-invited.html",
            {
                "request": request,
                "invitation_url": str(
                    await gen_guild_invite(891588026780770344)
                ),
            },
        )
