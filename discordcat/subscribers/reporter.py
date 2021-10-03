import json
import traceback
from datetime import datetime

from hikari.events import InteractionCreateEvent, ExceptionEvent

from .subscriber import Subscription
from ..audit.error_reporting import report_interaction_exception
from ..services import db


class ExceptionReporter(Subscription):
    event = ExceptionEvent

    async def callback(self, event: ExceptionEvent):
        exception_report = db["exceptions"].insert_one(
            {
                "occurred_at": datetime.now(),
                "event": str(event.failed_event),
                "exception": {
                    "repr": event.exception.__repr__(),
                    "traceback": "".join(
                        traceback.format_exception(
                            etype=type(event.exception),
                            value=event.exception,
                            tb=event.exception.__traceback__,
                        )
                    ),
                },
            }
        )

        if hasattr(event.failed_event, 'author'):
            db["exceptions"].update_one(
                {"_id": exception_report.inserted_id},
                {"$set": {"author": str(event.failed_event.author)}}
            )

        for oid in self.bot.owner_ids:
            owner = await self.bot.rest.fetch_user(oid)
            await owner.send(
                f"Wystąpił błąd! ```json\n{json.dumps({'id': str(exception_report.inserted_id), 'exception': repr(event.exception)}, indent=2)}\n```"
            )
