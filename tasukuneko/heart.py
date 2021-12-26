import logging
import os
from datetime import datetime

from asgiref.sync import async_to_sync
from celery import Celery
from celery.utils.log import get_task_logger
from dotenv import load_dotenv
from hikari import RESTApp

load_dotenv()

app = Celery('heart')
app.config_from_object('tasukuneko.settings')
app.conf.enable_utc = False


@app.task(name='pong')
def ping():
    async def body():
        async with RESTApp().acquire(os.getenv('DISCORD_TOKEN'), 'Bot') as client:
            user = await client.fetch_user(285146237613899776)
            await user.send(datetime.now().isoformat())
    async_to_sync(body)()


app.conf.beat_schedule = {
    'ping': {
        'task': 'pong',
        'schedule': 5.0
    }
}
