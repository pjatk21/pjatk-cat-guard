from hikari import Intents
from lightbulb import Bot

from .services import env
from .commands import *
from .subscribers import *
from .subscribers.starter import Starter

bot = Bot(
    token=env.get("DISCORD_TOKEN"),
    slash_commands_only=True,
    banner=None,
    logs="DEBUG",
    owner_ids=[285146237613899776],
    intents=Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS
)

# Slash commands
for slash_cmd in [
    SetupCommand,
    VerifyCommand,
    VerifyForceCommand,
    ManageGroup,
    SystemCheckCommand,
]:
    bot.add_slash_command(slash_cmd)

# Subscribers
for subscription in [Starter, NewUserJoined]:
    bot.subscribe(subscription.event, subscription.callback)
