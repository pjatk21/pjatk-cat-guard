import logging
import re

import yaml
from hikari.events import GuildMessageCreateEvent
from hikari.errors import ForbiddenError
from lightbulb import Plugin

plugin = Plugin('hehe funny responses')
logger = logging.getLogger('gadoneko.plugins.funny')

hehe_funny = []


def load(bot):
    global hehe_funny
    with open('gadoneko/static/funny.yml', 'r') as f:
        hehe_funny = yaml.safe_load(f)
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.listener(GuildMessageCreateEvent)
async def reply_for_match(event: GuildMessageCreateEvent):
    if event.content and event.is_human:
        for rule in hehe_funny:
            if re.search(rule['regex'], event.content) and not (event.channel_id in rule.get('whitelist', []) and event.channel_id in rule.get('blacklist', [])):
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
                if rule.get('dm'):
                    try:
                        await event.member.send(rule.get('dm'))
                    except ForbiddenError:
                        pass
                if rule.get('action'):
                    match rule['action']:
                        case 'delete':
                            await plugin.bot.rest.delete_message(event.channel_id, event.message_id)
                        case 'kick':
                            try:
                                await plugin.bot.rest.kick_member(event.guild_id, event.member, reason='Funny rule.')
                            except ForbiddenError:
                                await plugin.bot.rest.create_message(event.channel_id, f'{event.member.mention}, normalnie dałbym ci kopa w dupe, ale nie mam uprawnień.')
