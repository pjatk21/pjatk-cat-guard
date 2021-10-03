import traceback
from typing import Optional

from hikari import ExceptionEvent, CommandInteraction
from lightbulb import Bot

from discordcat.services import db


async def report_interaction_exception(event: ExceptionEvent, bot: Optional[Bot] = None):
    interaction: CommandInteraction = event.failed_event.interaction
    report_doc = db['exceptions'].insert_one(
        {
            "interaction": {
                "id": interaction.id,
                "date": interaction.created_at,
            },
            "guild": {
                "id": interaction.get_guild().id,
                "name": interaction.get_guild().name
            },
            "channel": {
                "id": interaction.get_channel().id,
                "name": interaction.get_channel().name
            },
            "user": {
                "id": interaction.user.id,
                "name": str(interaction.user),
            },
            "exception": {
                "repr": event.exception.__repr__(),
                "traceback": ''.join(
                    traceback.format_exception(
                        etype=type(event.exception), value=event.exception, tb=event.exception.__traceback__
                    )
                )
            }
        }
    )

    if bot is not None:
        for oid in bot.owner_ids:
            owner = await bot.rest.fetch_user(oid)
            await owner.send(f"```{event.exception}``````{event.failed_event}``````{report_doc.inserted_id}```")
