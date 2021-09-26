from lightbulb import Bot

from discordcat.configure import SetupCommand
from discordcat.services import env
from discordcat.update import UpdateCommand
from discordcat.verifing import VerifyCommand
from discordcat.manage import ManageGroup

bot = Bot(token=env.get("DISCORD_TOKEN"), slash_commands_only=True, banner=None)


bot.add_slash_command(SetupCommand)
bot.add_slash_command(UpdateCommand)
bot.add_slash_command(VerifyCommand)
bot.add_slash_command(ManageGroup)

bot.run()
