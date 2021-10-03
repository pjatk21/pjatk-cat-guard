import logging

from hikari.events import MemberCreateEvent
from .subscriber import Subscription


class NewUserJoined(Subscription):
    event = MemberCreateEvent

    async def callback(self, event: MemberCreateEvent):
        logging.getLogger("new-member").debug(
            f"New member {event.member} joined, sending welcome message."
        )
        await event.member.send(
            "uwu, na tym serwerze obowiązuje weryfikacja!\n"
            'Sprawdź kanał "#✋weryfikacja-członków" aby dowiedzieć się więcej uwu'
        )
