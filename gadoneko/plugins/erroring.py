from datetime import datetime

from hikari import Embed
from lightbulb import Plugin
from lightbulb.events import SlashCommandErrorEvent

from shared.colors import ERR
from shared.formatting import code_block

plugin = Plugin('Errors handling')


def load(bot):
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

    raise event.exception
