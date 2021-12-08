import asyncio
import logging
import os

import aiocron
import millify
from aiohttp import ClientSession
from dotenv import load_dotenv
from hikari import RESTApp, Embed

from shared.colors import RESULT

load_dotenv()
loop = asyncio.new_event_loop()
logger = logging.getLogger('gadoneko.cron')
logging.basicConfig(level=logging.INFO, format='%(levelname)-1.1s %(asctime)23.23s %(name)s: %(message)s')

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

logger.info('Starting loop...')
loop.run_forever()
