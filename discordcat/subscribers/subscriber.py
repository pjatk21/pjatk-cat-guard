from abc import ABC, abstractmethod

from hikari.events import Event
from lightbulb import Bot


class Subscription(ABC):
    def __init__(self, bot: Bot):
        self.bot = bot

    @property
    @abstractmethod
    def event(self) -> Event:
        ...

    @abstractmethod
    async def callback(self, event: Event):
        ...
