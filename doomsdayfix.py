import asyncio
import os

from dotenv import load_dotenv
from hikari import GatewayBot, ShardReadyEvent, HikariError, Embed, Member
from mongoengine import DoesNotExist, FieldDoesNotExist

from gadoneko.plugins.trust import start_verification_flow

from shared.db import init_connection
from shared.documents import VerificationRequest, TrustedUser

load_dotenv()
init_connection()

bot = GatewayBot(os.getenv('DISCORD_TOKEN'))


@bot.listen(ShardReadyEvent)
async def doomsday_fix(event: ShardReadyEvent):
    guild = await bot.rest.fetch_guild(872492754821861387)
    # 891384663933878272 is trusted
    members_affected: tuple[Member] = tuple(filter(
        lambda m: 891384663933878272 not in m.role_ids, await bot.rest.fetch_members(guild)
    ))

    for m in members_affected:
        try:
            TrustedUser.objects(identity__user_id=m.id).get().delete()
            print('fix 🔧', m)
        except DoesNotExist:
            pass

