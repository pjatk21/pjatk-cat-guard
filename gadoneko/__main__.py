from gadoneko.bot import bot
from shared.db import init_connection

init_connection()

bot.run()
