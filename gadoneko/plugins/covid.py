import os

import millify
from aiohttp import ClientSession
from hikari import GuildMessageCreateEvent, Embed
from lightbulb import Plugin

from shared.colors import RESULT

plugin = Plugin('COVID tracker')


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.listener(GuildMessageCreateEvent)
async def covid_mentioned(event: GuildMessageCreateEvent):
    # Return if message is from bot or don't have content
    if event.author.is_bot or event.author.is_system or event.message.content is None:
        return

    if (not os.getenv('APIFY_COVID')) or ('statystyki covid' not in event.message.content.lower()):
        return

    embed = Embed(
        title='COVID 19 (statystyki)', description='Dane rządowe', color=RESULT
    )

    extract_keys = (
        ('dailyInfected', 'Zakażono dziś'),
        ('dailyTested', 'Przetestowano dziś'),
        # ('dailyPositiveTests', 'Potwierdzone z testów'),
        ('dailyDeceased', 'Zmarło dziś'),
        ('dailyRecovered', 'Wyzdrowiało dziś'),
        ('infected', 'Zakażono'),
        ('deceased', 'Zmarło'),
        ('recovered', 'Wyzdrowiało'),
        ('dailyQuarantine', 'Wysłano na kwarantannę')
    )

    async with ClientSession() as session:
        async with session.get(os.getenv('APIFY_COVID')) as response:
            data = await response.json()
            for ext_key, title in extract_keys:
                embed.add_field(title, millify.millify(data[ext_key], 1))

            embed.set_footer(f'Ostatnia aktualizajca danych: {data["txtDate"]}')

    await event.message.respond(
        embed=embed
    )
