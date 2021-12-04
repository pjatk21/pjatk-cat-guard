from lightbulb import Plugin
from lightbulb.events import SlashCommandErrorEvent

from discordcat.embed_factory import embed_error

plugin = Plugin('Errors handling')


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.listener(SlashCommandErrorEvent)
async def slash_err(event: SlashCommandErrorEvent):
    err_embed = embed_error(str(event.exception))
    err_embed.add_field('Error class', repr(event.exception.__class__))
    err_embed.add_field('Error cause class', repr(event.exception.__cause__.__class__))
    await event.context.respond(
        embed=err_embed
    )
    if event.exception.__cause__:
        await event.bot.rest.create_message(
            event.context.channel_id, f'```{str(event.exception.__cause__)}```'
        )
    raise event.exception
