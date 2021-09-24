import os

from dotenv import load_dotenv
from lightbulb import Bot

from discord_janitor.verifing import VerifyCommand, FallbackVerification

load_dotenv()

env = os.environ

bot = Bot(token=env.get("DISCORD_TOKEN"), slash_commands_only=True)


bot.add_slash_command(VerifyCommand)
bot.add_slash_command(FallbackVerification)

bot.run()
