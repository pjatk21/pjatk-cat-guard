import os

from dotenv import load_dotenv
from hikari import Intents
from lightbulb import BotApp

load_dotenv()

bot = BotApp(os.getenv('DISCORD_TOKEN'), intents=Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS)
bot.load_extensions('gadoneko.plugins.erroring')
bot.load_extensions('gadoneko.plugins.trust')

