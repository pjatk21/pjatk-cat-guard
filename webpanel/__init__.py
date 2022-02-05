import logging
import os

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from .panel import app

if os.getenv('SENTRY'):
    sentry_sdk.init(dsn=os.getenv('SENTRY'))
    app = SentryAsgiMiddleware(app)
    logging.info('Enabled sentry for webpanel (%s)', app)
