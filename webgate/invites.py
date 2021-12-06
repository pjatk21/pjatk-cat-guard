import os
from datetime import timedelta

from hikari import RESTApp


async def gen_guild_invite(channel_id: int):
    rest_app = RESTApp()
    async with rest_app.acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
        return await bot.create_invite(
            channel_id, max_uses=1, max_age=timedelta(minutes=5), reason="autogen"
        )
