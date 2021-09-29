from abc import ABC, abstractmethod
from hikari.events import Event


class Subscription(ABC):
    @property
    @abstractmethod
    def event(self) -> Event:
        ...

    @staticmethod
    @abstractmethod
    async def callback(event: Event):
        ...
