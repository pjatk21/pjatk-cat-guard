from hikari import CommandInteraction

from .subscriber import Subscription
from hikari.events import InteractionCreateEvent, ExceptionEvent

from ..audit.error_reporting import report_interaction_exception
from ..embed_factory import embed_error


class ExceptionReporter(Subscription):
    event = ExceptionEvent

    async def callback(self, event: ExceptionEvent):
        if isinstance(event.failed_event, InteractionCreateEvent):
            await report_interaction_exception(event, self.bot)
        else:
            for oid in self.bot.owner_ids:
                owner = await self.bot.rest.fetch_user(oid)
                await owner.send(f"```{event.exception}``````{event.failed_event}```")
