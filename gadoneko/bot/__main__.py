import logging
import os

import sentry_sdk as sentry
from requests import __version__

from gadoneko.bot import bot
from shared.db import init_connection

init_connection()

if os.getenv('SENTRY'):  # Init error reporting to sentry
    logging.info('Sentry DSN present, init.')
    sentry.init(os.getenv('SENTRY'), environment=os.getenv('ENV'), release=__version__)

if os.getenv('ENV') == 'dev':
    import warnings
    warnings.simplefilter('ignore', DeprecationWarning)
    bot.run(asyncio_debug=True, coroutine_tracking_depth=20, propagate_interrupts=True)
else:
    bot.run()
