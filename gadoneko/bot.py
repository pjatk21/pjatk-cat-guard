import os

from hikari import Intents
from lightbulb import BotApp
from dotenv import load_dotenv

load_dotenv()


bot = BotApp(os.getenv('DISCORD_TOKEN'), intents=Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS)
bot.load_extensions('plugins.trust')
bot.run()
