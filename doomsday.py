import asyncio
import os

from dotenv import load_dotenv
from hikari import GatewayBot, ShardReadyEvent, HikariError


load_dotenv()

bot = GatewayBot(os.getenv('DISCORD_TOKEN'))


@bot.listen(ShardReadyEvent)
async def doomsday(event: ShardReadyEvent):
    guild = await bot.rest.fetch_guild(872492754821861387)
    takedowns = [
        891384663933878272, 872855213525061662, 874665726886170695, 880770355520741376
    ]

    for member in await bot.rest.fetch_members(guild):
        try:
            await asyncio.gather([
                bot.rest.remove_role_from_member(
                    guild, member, role
                ) for role in takedowns
            ])
        except HikariError as he:
            print(he)
