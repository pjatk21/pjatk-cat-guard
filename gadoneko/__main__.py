import logging
import os

import sentry_sdk as sentry

from gadoneko.bot import bot
from shared.db import init_connection

init_connection()

if os.getenv('SENTRY'):  # Init error reporting to sentry
    logging.info('Sentry DSN present, init.')
    sentry.init(os.getenv('SENTRY'), environment=os.getenv('ENV'))

bot.run()
