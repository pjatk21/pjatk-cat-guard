import asyncio
import logging
import os
from datetime import datetime, timedelta
import random
from pathlib import Path

import aiocron
import millify
import yaml
from aiohttp import ClientSession
from dotenv import load_dotenv
from hikari import RESTApp, Embed, Member
from hikari.errors import NotFoundError, RateLimitedError, ForbiddenError

from shared.util import chunks
from shared.colors import RESULT, OK
from shared.db import init_connection
from shared.documents import CronHealthCheck
import sentry_sdk as sentry
from gadoneko._metadata import __version__
from shared.formatting import code_block

load_dotenv()

loop = asyncio.new_event_loop()
logger = logging.getLogger('gadoneko.cron')
if os.getenv('ENV') == 'dev':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-1.1s %(asctime)23.23s %(name)s: %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(levelname)-1.1s %(asctime)23.23s %(name)s: %(message)s')

if os.getenv('SENTRY'):  # Init error reporting to sentry
    logging.info('Sentry DSN present, init.')
    sentry.init(os.getenv('SENTRY'), environment=os.getenv('ENV'), release=__version__)

init_connection()


@aiocron.crontab('11 11 * * *', loop=loop)
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

    async with RESTApp().acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as client:
        covid_message = await client.create_message(
            os.getenv('COVID_UPDATES', 918167880535773194),
            embed=embed
        )
        await client.crosspost_message(covid_message.channel_id, covid_message.id)


@aiocron.crontab('*/5 * * * *', loop=loop)
async def health_check():
    logger.debug('Updating health checks...')
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

    async with RESTApp().acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as client:
        await asyncio.gather(
            *[update(widget) for widget in widgets]
        )


@aiocron.crontab("14 14 24 12 *", loop=loop)
async def happy_christmas(repeat: Member = None):
    with open(Path.cwd().joinpath('shared/festive.yml'), 'r') as file:
        wishes: list[str] = yaml.safe_load(file)

    async def try_sending_wish(member: Member):
        try:
            logger.debug('Sending message to the %s...', str(member))
            await member.send(
                f"Administracja PJATK'owego serwera discord z okazji świąt życzy "
                f"spokojnie spędzonej wigilii, zdanych studiów, szczęśliwego nowego roku, zdrowia oraz "
                f"{random.choice(wishes)}"
            )
        except RateLimitedError as rle:
            # Probably redundant, because ✨superior hikari✨ does it anyway
            logger.warning('Rate limit reached, next call will be at %s', (datetime.now() + timedelta(seconds=rle.retry_after)).isoformat())
            await asyncio.sleep(rle.retry_after + 1)
            await happy_christmas.func(member)  # wait and retry
        except ForbiddenError as fe:
            logger.warning('User %s has blocked DM, skipping... (%s)', str(member), fe.message)
        except Exception as err:
            logger.error(err)  # Kids, don't do it this way, please, it's illegal like drugs and genocide

    async with RESTApp().acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as client:
        if repeat:
            await try_sending_wish(repeat)

        guild = await client.fetch_guild(os.getenv('WISH_GUILD', 635437057858076682))
        members = [member for member in await client.fetch_members(guild) if not member.is_bot]
        logger.info('Sending wishes to %s members', len(members))
        chs = tuple(chunks(members, 12))
        for i, members_chunk in enumerate(chs):
            logger.info('Chunk %s of %s (%s)', i+1, len(chs), f'{(i+1)/len(chs) * 100:.2f}%')
            await asyncio.gather(*[try_sending_wish(member) for member in members_chunk])

logger.info('Starting loop...')
logger.info('The soonest possible exec will be in %s seconds.', 60 - datetime.now().second)
loop.run_forever()
