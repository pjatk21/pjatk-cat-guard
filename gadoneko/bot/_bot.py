import os

import yaml
from dotenv import load_dotenv
from hikari import Intents, Status, Activity, ActivityType, Embed
from hikari.events import ShardReadyEvent, ShardDisconnectedEvent
from lightbulb import BotApp, add_checks, Check, command, commands, implements, Context

from doctor import DockerDoctor
from gadoneko.checks import bot_owner_only

load_dotenv()

if os.getenv('ENV') == 'dev':
    bot = BotApp(os.getenv('DISCORD_TOKEN'), intents=Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS, logs='INFO')
else:
    bot = BotApp(os.getenv('DISCORD_TOKEN'), intents=Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS)

bot.load_extensions_from('gadoneko/plugins')


@bot.command()
@add_checks(Check(bot_owner_only))
@command('reload', 'Uruchamia ponownie bota')
@implements(commands.SlashCommand)
async def reload(ctx: Context):
    bot.reload_extensions(*bot.extensions)
    embed = Embed(title='Przeładowano wtyczki', description=yaml.dump(bot.extensions))
    await ctx.respond(embed=embed)


@bot.listen(ShardReadyEvent)
async def ready(event: ShardReadyEvent):
    if os.getenv('MOTD'):
        await event.shard.update_presence(
            status=Status.ONLINE,
            activity=Activity(name=os.getenv('MOTD'), type=ActivityType.PLAYING)
        )

    DockerDoctor('bot').update_module('bot')


@bot.listen(ShardDisconnectedEvent)
async def mark_not_healthy(event: ShardDisconnectedEvent):
    DockerDoctor('bot').fail_module('bot')

