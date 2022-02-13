import logging
import re
import subprocess

import yaml
from hikari.events import GuildMessageCreateEvent
from hikari.errors import ForbiddenError
from lightbulb import Plugin, command, implements, commands, Context, option

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
            if rule.get('whitelist'):
                if event.channel_id not in rule['whitelist']:
                    continue

            if rule.get('blacklist'):
                if event.channel_id in rule['blacklist']:
                    continue

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


__cows = ['cheese', 'suse', 'amogus', 'tux', 'vader', 'cock', 'default', 'moose', 'moofasa']
__cows.sort()


@plugin.command()
@option('character', 'Wybierz postać', choices=__cows, default='default')
@option('text', 'To co powie krowa', type=str)
@command('cowsay', 'Krowa mądrze ci powie')
@implements(commands.MessageCommand, commands.SlashCommand)
async def cowsay(ctx: Context):
    text = ctx.options.text or ctx.options.target.content or 'None'
    cow = ctx.options.character or 'default'

    result = subprocess.check_output(
        ['cowsay', '-f', cow, text]
    ).decode()

    await ctx.respond(
        f'```\n{result}\n```'
    )


__fonts = [
    'doom', 'standard', 'starwars', 'mini', 'epic', 'digital', 'wavy', 'morse'
]
__fonts.sort()


@plugin.command()
@option('custom-font', 'Specjalna czcionka figleta', required=False)
@option('font', 'Czcionka dla figleta', choices=__fonts, required=False, default='standard')
@option('text', 'Cool text', type=str)
@command('figlet', 'Super cool text')
@implements(commands.MessageCommand, commands.SlashCommand)
async def figlet(ctx: Context):
    text = ctx.options.text or ctx.options.target.content or 'None'
    font = ctx.options.font or ctx.options.custom_font or 'standard'

    result = subprocess.check_output(
        ['figlet', '-f', font, text]
    ).decode()

    await ctx.respond(
        f'```\n{result}\n```'
    )

