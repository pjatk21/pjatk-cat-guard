import asyncio
import os

from dotenv import load_dotenv
from hikari import GatewayBot, ShardReadyEvent, HikariError, Embed
from mongoengine import DoesNotExist

from gadoneko.plugins.trust import start_verification_flow

from shared.db import init_connection
from shared.documents import VerificationRequest, TrustedUser

load_dotenv()
init_connection()

bot = GatewayBot(os.getenv('DISCORD_TOKEN'))


@bot.listen(ShardReadyEvent)
async def doomsday(event: ShardReadyEvent):
    guild = await bot.rest.fetch_guild(872492754821861387)
    takedowns = [
        891384663933878272, 872855213525061662, 874665726886170695, 880770355520741376
    ]

    for member in await bot.rest.fetch_members(guild):
        try:
            trust: TrustedUser = TrustedUser.objects(identity__user_id=member.id, identity__guild_id=guild.id).get()
        except DoesNotExist:
            continue

        trust.delete()

        vr: VerificationRequest = start_verification_flow(guild, member)
        link = f"{os.getenv('VERIFICATION_URL')}verify/{vr.code}"

        try:
            await asyncio.gather(*[
                bot.rest.remove_role_from_member(
                    guild, member, role
                ) for role in takedowns
            ], member.send(
                embed=Embed(
                    title='Nowy link weryfikacyjny!',
                    description=f'Oto twój nowy link: {link}, przypominamy również, że rangi typ "Warszawa Dzienne", trzeba ponownie przypisać',
                    url=link,
                ).set_footer('doomsday')
            ))
            print('reset ✅', member)
        except HikariError as he:
            print(he, member)
