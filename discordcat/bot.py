from lightbulb import Bot

from discordcat.configure import SetupCommand
from discordcat.services import env
from discordcat.verifing import VerifyCommand, VerifyForceCommand
from discordcat.manage import ManageGroup

bot = Bot(token=env.get("DISCORD_TOKEN"), slash_commands_only=True, banner=None, logs="DEBUG")


bot.add_slash_command(SetupCommand)
bot.add_slash_command(VerifyCommand)
bot.add_slash_command(VerifyForceCommand)
bot.add_slash_command(ManageGroup)
