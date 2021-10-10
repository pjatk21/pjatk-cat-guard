import functools
import logging

from lightbulb import SlashCommandContext

logger = logging.getLogger("checks")


def audit_check():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(context: SlashCommandContext):
            logger.debug(
                f"{str(context.author)} is trying to pass {func.__name__} check"
            )
            result = await func(context)
            if result is False:
                logger.warning(
                    f"{str(context.author)} has failed {func.__name__} check!"
                )
                await context.author.send(
                    f"Próbujesz wywołać komendę, ale kontekst wywołania nie jest poprawny! Test, który zwrócił wartość `False`: {func.__name__}."
                )
            return result

        return wrapped

    return wrapper
