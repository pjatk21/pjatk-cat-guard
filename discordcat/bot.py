from lightbulb import Bot

from .services import env
from .commands import *
from .subscribers import *

bot = Bot(
    token=env.get("DISCORD_TOKEN"), slash_commands_only=True, banner=None, logs="DEBUG"
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
for subscription in [CheckUser, NewUserJoined]:
    bot.subscribe(subscription.event, subscription.callback)
