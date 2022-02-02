import os

from dotenv import load_dotenv
from hikari import Intents, Status, Activity, ActivityType
from hikari.events import ShardReadyEvent, ShardDisconnectedEvent
from lightbulb.events import CommandInvocationEvent
from lightbulb import BotApp
from doctor import DockerDoctor

load_dotenv()

if os.getenv('ENV') == 'dev':
    bot = BotApp(os.getenv('DISCORD_TOKEN'), intents=Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS, logs='DEBUG')
else:
    bot = BotApp(os.getenv('DISCORD_TOKEN'), intents=Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS)

bot.load_extensions_from('gadoneko/plugins')


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

