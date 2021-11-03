from hikari import Intents
from lightbulb import Bot

from discordcat.commands.setup.bot_init import init_bot_guild
from .commands import *
from .commands.findby import FindBy
from .commands.verifing import test_form
from .services import env
from .subscribers import *
from .subscribers.explain import Explainer
from .subscribers.reporter import ExceptionReporter
from .subscribers.starter import Starter

bot = Bot(
    token=env.get("DISCORD_TOKEN"),
    prefix="gadoneko ",
    banner=None,
    logs="DEBUG",
    owner_ids=[285146237613899776],
    intents=Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS,
)

for legacy_cmd, invc_name in [(init_bot_guild, "init"), (test_form, "tf")]:
    bot.add_command(legacy_cmd, name=invc_name)

# Slash commands
for slash_cmd in [
    SetupCommand,
    VerifyCommand,
    # VerifyForceCommand,
    ManageGroup,
    SystemCheckCommand,
    FindBy,
]:
    bot.add_slash_command(slash_cmd)

# Subscribers
for subscription in [Starter, NewUserJoined, ExceptionReporter, Explainer]:
    initialised_subscriber = subscription(bot)
    bot.subscribe(initialised_subscriber.event, initialised_subscriber.callback)
