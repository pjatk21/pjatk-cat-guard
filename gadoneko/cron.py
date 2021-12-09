import asyncio
import logging
import os
from datetime import datetime, timedelta

import aiocron
import millify
import yaml
from aiohttp import ClientSession
from dotenv import load_dotenv
from hikari import RESTApp, Embed
from hikari.errors import NotFoundError

from shared.colors import RESULT, OK
from shared.db import init_connection
from shared.documents import CronHealthCheck
import sentry_sdk as sentry
from gadoneko._metadata import __version__
from shared.formatting import code_block

load_dotenv()

loop = asyncio.new_event_loop()
logger = logging.getLogger('gadoneko.cron')
logging.basicConfig(level=logging.INFO, format='%(levelname)-1.1s %(asctime)23.23s %(name)s: %(message)s')

if os.getenv('SENTRY'):  # Init error reporting to sentry
    logging.info('Sentry DSN present, init.')
    sentry.init(os.getenv('SENTRY'), environment=os.getenv('ENV'), release=__version__)

init_connection()
bot = RESTApp()


@aiocron.crontab('45 11 * * *', loop=loop)
# @aiocron.crontab('* * * * *', loop=loop)
async def announce_covid_stats():
    logger.info('Sending embed')
    embed = Embed(
        title='COVID 19 (statystyki)', description='Dane rządowe', color=RESULT
    )

    extract_keys = (
        ('dailyInfected', 'Zakażono dziś'),
        ('dailyTested', 'Przetestowano dziś'),
        ('dailyDeceased', 'Zmarło dziś'),
        ('dailyRecovered', 'Wyzdrowiało dziś'),
        ('dailyQuarantine', 'Obecnie na kwarantannie')
    )

    async with ClientSession() as session:
        async with session.get(os.getenv('APIFY_COVID')) as response:
            data = await response.json()
            for ext_key, title in extract_keys:
                embed.add_field(title, millify.millify(data[ext_key], 1))

            embed.set_footer(f'Ostatnia aktualizajca danych: {data["txtDate"]}')

    async with bot.acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as client:
        await client.create_message(
            918167880535773194,  # TODO: remove hard code
            embed=embed
        )


@aiocron.crontab('*/5 * * * *', loop=loop)
async def health_check():
    heartbeat = datetime.now()
    widget_embed = Embed(
        title='CRON healthcheck',
        description=code_block(
            yaml.dump({'heartbeat': heartbeat.isoformat(), 'next': (heartbeat + timedelta(minutes=5)).isoformat()}),
            flavour='yaml'
        ),
        color=OK,
    )

    widgets = CronHealthCheck.objects()

    async def update(widget):
        try:
            await client.edit_message(
                widget.widget_channel_id, widget.widget_message_id, content=None, embed=widget_embed
            )
            logger.info('Widget %s updated!', widget.widget_message_id)
        except NotFoundError:
            logger.info('Message %s removed, remove widget check!', widget.widget_message_id)
            widget.delete()

    async with bot.acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as client:
        await asyncio.gather(
            *[update(widget) for widget in widgets]
        )

logger.info('Starting loop...')
loop.run_forever()
