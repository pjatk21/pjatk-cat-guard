from lightbulb import Bot

from discordcat.configure import SetupCommand
from discordcat.services import env
from discordcat.update import UpdateCommand
from discordcat.verifing import VerifyCommand, AboutMeCommand, InvalidateCommand

bot = Bot(token=env.get("DISCORD_TOKEN"), slash_commands_only=True, banner=None)


bot.add_slash_command(SetupCommand)
bot.add_slash_command(UpdateCommand)
bot.add_slash_command(VerifyCommand)
bot.add_slash_command(InvalidateCommand)
bot.add_slash_command(AboutMeCommand)

bot.run()
