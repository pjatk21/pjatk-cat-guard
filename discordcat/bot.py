from lightbulb import Bot

from .commands.configure import SetupCommand
from .services import env
from .commands.verifing import VerifyCommand, VerifyForceCommand
from .commands.manage import ManageGroup
from .commands.system import SystemCheckCommand

bot = Bot(token=env.get("DISCORD_TOKEN"), slash_commands_only=True, banner=None, logs="DEBUG")

bot.add_slash_command(SetupCommand)
bot.add_slash_command(VerifyCommand)
bot.add_slash_command(VerifyForceCommand)
bot.add_slash_command(ManageGroup)
bot.add_slash_command(SystemCheckCommand)
