import logging
import os

from lightbulb import Plugin, BotApp, command, implements, commands, Context
from mongoengine import DoesNotExist

from shared.documents import AltapiConfiguration, UserIdentity

plugin = Plugin('Altapi')
logger = logging.getLogger('gadoneko.altapi')
BASE_URL = 'https://altapi.kpostek.dev/v1'


def load(bot: BotApp):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.command()
@command('altapi-config', 'Skonfiguruj usługę altapi', ephemeral=True)
@implements(commands.SlashCommand)
async def altapi_config(ctx: Context):
    try:
        ac = AltapiConfiguration.objects(identity__user_id=ctx.user.id).get()
    except DoesNotExist:
        ac = AltapiConfiguration(identity=UserIdentity.from_context(ctx))
        ac.save()
    await ctx.respond(f"{os.getenv('VERIFICATION_URL')}altapi/configure/{ac.id}")


@plugin.command()
@command('timetable', 'Pobierz plan zajęć na kolejny dzień')
@implements(commands.SlashCommand)
async def timetable(ctx: Context):
    pass
