from hikari.events import MemberCreateEvent
from .subscriber import Subscription


class NewUserJoined(Subscription):
    event = MemberCreateEvent

    @staticmethod
    async def callback(event: MemberCreateEvent):
        await event.member.send(
            "uwu, na tym serwerze obowiązuje weryfikacja!\n"
            "Sprawdź kanał \"#✋weryfikacja-członków\" aby dowiedzieć się więcej uwu"
        )
