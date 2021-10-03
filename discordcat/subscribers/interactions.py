from hikari import CommandInteraction

from .subscriber import Subscription
from hikari.events import InteractionCreateEvent, ExceptionEvent

from ..audit.error_reporting import report_exception_event
from ..embed_factory import embed_error


class ExceptionReporter(Subscription):
    event = ExceptionEvent

    async def callback(self, event: ExceptionEvent):
        if isinstance(event.failed_event.interaction, CommandInteraction):
            await report_exception_event(event, self.bot)
