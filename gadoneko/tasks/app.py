import asyncio
import json
import logging
import os
import functools
from datetime import timedelta, datetime

import millify
from aiohttp import ClientSession
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_logger
from hikari import Embed, RESTApp, ForbiddenError
from httpx import AsyncClient

import webpanel.tasks
from shared.colors import RESULT
from shared.db import init_connection
from shared.documents import VerificationRequest, VerificationState, VerificationRejection
from shared.graphs import create_graph

app = Celery('gadoneko', broker=os.getenv('RABBITMQ_URL', 'amqp://localhost//'))
logger = get_logger('gadoneko.tasks')

app.conf.beat_schedule = {
    'covid-news': {
        'task': 'covid-news',
        'schedule': crontab(hour=11, minute=5),
        'options': {
            'expires': timedelta(hours=12).total_seconds()
        }
    },
    'remove-dandling': {
        'task': 'clean-dandling-verifications',
        'schedule': crontab(minute='*/10'),
        'options': {
            'expires': timedelta(minutes=5).total_seconds()
        }
    }
}
app.conf.timezone = os.getenv('TZ', 'Europe/Warsaw')


def async_to_sync(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapped


@app.task(name='covid-news')
@async_to_sync
async def covid_news():
    logger.info('Sending covid embed...')
    embed = Embed(
        title='COVID 19 (statystyki)', description='Dane rządowe', color=RESULT
    )

    extract_keys = (
        ('dailyPositiveTests', 'Zakażono dziś'),
        ('dailyTested', 'Przetestowano dziś'),
        ('dailyDeceased', 'Zmarło dziś'),
        ('dailyRecovered', 'Wyzdrowiało dziś'),
        ('dailyQuarantine', 'Obecnie na kwarantannie')
    )

    covid_client = AsyncClient()
    covid_hist: list[dict] = (await covid_client.get(os.getenv('APIFY_COVID'))).json()
    covid_hist.reverse()
    covid_today = covid_hist[-1]

    for ext_key, title in extract_keys:
        embed.add_field(title, millify.millify(covid_today[ext_key], 1))

    embed.set_image(create_graph(covid_hist).to_image(format='png'))

    embed.set_footer(f'Ostatnia aktualizajca danych: {covid_today["txtDate"]}')

    async with RESTApp().acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as client:
        covid_message = await client.create_message(
            os.getenv('COVID_UPDATES', 918167880535773194),
            embed=embed
        )
        logger.info('Covid embed sent!')
        try:
            await client.crosspost_message(covid_message.channel_id, covid_message.id)
            logger.info('Covid embed crossposted!')
        except ForbiddenError:
            logger.info("Can't crosspost covid embed.")

    await covid_client.aclose()


@app.task(name='clean-dandling-verifications')
@async_to_sync
async def clean_dandling_vrs():
    init_connection()

    deadline = datetime.now() - timedelta(days=2)
    results = VerificationRequest.objects(state=VerificationState.ID_REQUIRED, submitted__lte=deadline)
    logger.info('Removing %s dandling accounts!', len(results))

    for vr in results:
        vr: VerificationRequest = vr
        vr.state = VerificationState.REJECTED
        rejection_message = '[AUTO] czas na przesłanie (48h) dokumentów minął'
        vr.rejection = VerificationRejection(reason=rejection_message)
        vr.save()
        await asyncio.gather(
            webpanel.tasks.send_rejection_dm(vr, rejection_message),
            webpanel.tasks.send_rejection_mail(vr, rejection_message)
        )

if __name__ == '__main__':
    clean_dandling_vrs.delay()
