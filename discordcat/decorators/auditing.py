import functools
import logging

from lightbulb import SlashCommandContext

logger = logging.getLogger("checks")


def audit_check():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(context: SlashCommandContext):
            logger.debug(f"{str(context.author)} is trying to pass {func.__name__} check")
            result = await func(context)
            if result is False:
                logger.warning(f"{str(context.author)} has failed {func.__name__} check!")
                owner = await context.bot.rest.fetch_user(285146237613899776)
                await owner.send(f"{str(context.author)} has failed {func.__name__} check!")
            return result
        return wrapped
    return wrapper
