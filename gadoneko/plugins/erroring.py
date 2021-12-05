import logging
import os
from datetime import datetime

import sentry_sdk as sentry
from hikari import Embed
from lightbulb import Plugin
from lightbulb.events import SlashCommandErrorEvent

from shared.colors import ERR
from shared.formatting import code_block

plugin = Plugin('Errors handling')
logger = logging.getLogger('gadoneko.plugins.erroring')


def load(bot):
    if os.getenv('SENTRY'):  # Init error reporting
        sentry.init(os.getenv('SENTRY'))
        logger.info('Sentry SDK enabled')
    else:
        logger.info('No SENTRY DSN presented, skipping init')

    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.listener(SlashCommandErrorEvent)
async def slash_err(event: SlashCommandErrorEvent):
    err_embed = Embed(title='⚠️ Błąd', description=str(event.exception), color=ERR, timestamp=datetime.now().astimezone())
    err_embed.add_field('Error class', f'`{repr(event.exception.__class__)}`')
    if event.exception.__cause__:
        err_embed.add_field('Cause class', f'`{repr(event.exception.__cause__.__class__)}`')

    await event.context.respond(
        embeds=[err_embed, Embed(description=code_block(str(event.exception.__cause__)), color=ERR)] if event.exception.__cause__ else [err_embed]
    )

    if os.getenv('SENTRY'):
        with sentry.push_scope() as scope:
            scope.set_user({'username': str(event.context.user)})
            sentry.capture_exception(event.exception.__cause__ if event.exception.__cause__ else event.exception)
    else:
        raise event.exception
