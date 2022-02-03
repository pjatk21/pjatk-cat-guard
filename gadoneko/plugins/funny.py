import logging
import re

import yaml
from hikari import CustomEmoji
from lightbulb import Plugin
from hikari.events import GuildMessageCreateEvent

plugin = Plugin('hehe funny responses')
logger = logging.getLogger('gadoneko.plugins.funny')

hehe_funny = []


def load(bot):
    global hehe_funny
    with open('static/funny.yml', 'r') as f:
        hehe_funny = yaml.safe_load(f)
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.listener(GuildMessageCreateEvent)
async def reply_for_match(event: GuildMessageCreateEvent):
    if event.content and event.is_human:
        for rule in hehe_funny:
            if re.search(rule['regex'], event.content):
                if rule.get('reply'):
                    await plugin.bot.rest.create_message(
                        event.channel_id,
                        rule.get('reply'),
                        reply=event.message_id
                    )
                if rule.get('send'):
                    await plugin.bot.rest.create_message(
                        event.channel_id,
                        rule.get('send')
                    )
                if rule.get('reaction') and rule.get('guild'):
                    await plugin.bot.rest.add_reaction(
                        event.channel_id,
                        event.message_id,
                        emoji=(await plugin.bot.rest.fetch_guild(rule.get('guild'))).get_emoji(rule.get('reaction')),
                    )
                if rule.get('reaction') and not rule.get('guild'):
                    await plugin.bot.rest.add_reaction(
                        event.channel_id,
                        event.message_id,
                        emoji=rule.get('reaction')
                    )
