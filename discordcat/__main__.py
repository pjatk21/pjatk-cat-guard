import logging

from discordcat.bot import bot
from discordcat.services import mongo
from discordcat.services import env

local_logger = logging.getLogger("module-runner")

if not env.get('DISABLE_TEST'):
    local_logger.debug("Testing connection to the mongo...")
    mongo.list_database_names()
    local_logger.debug("Runner passed initial tests")
else:
    local_logger.debug("Skippking tests...")

logging.info("Starting bot")
bot.run()
