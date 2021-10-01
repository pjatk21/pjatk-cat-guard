from hikari import Status, Activity, ActivityType
from hikari.events import ShardReadyEvent

from .subscriber import Subscription


class Starter(Subscription):
    event = ShardReadyEvent

    @staticmethod
    async def callback(event: ShardReadyEvent):
        await event.shard.update_presence(
            status=Status.ONLINE,
            activity=Activity(name="I TAK nie zdasz", type=ActivityType.WATCHING),
        )
