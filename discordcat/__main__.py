import logging

from discordcat.bot import bot
from discordcat.services import mongo

local_logger = logging.getLogger("module-runner")

local_logger.debug("Testing connection to the mongo...")
mongo.list_database_names()
local_logger.debug("Runner passed initial tests")

logging.info("Starting bot")
bot.run()
