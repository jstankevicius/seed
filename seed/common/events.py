from abc import ABC
from collections import deque
from dataclasses import dataclass
from seed.common.base_types import *


@dataclass
class Event(ABC):
    pass


class EventBus:
    def __init__(self):
        # Event -> list[callable]
        self._listeners = {}
        self._queue = deque()

    def subscribe(self, event_type: type[Event], callback: callable) -> None:
        self._listeners.setdefault(event_type, []).append(callback)

    def publish(self, event: Event) -> None:
        self._queue.append(event)

    def dispatch(self) -> None:
        while self._queue:
            event = self._queue.popleft()
            for callback in self._listeners.get(type(event), []):
                callback(event)


@dataclass
class SystemOwnerChangedEvent(Event):
    # Do these need to be entities or can they be concrete components?
    system: Entity
    old_owner: Entity
    new_owner: Entity


@dataclass
class FleetStartedRouteToSystemEvent(Event):
    fleet: Entity
    source: Entity
    target: Entity


@dataclass
class FleetArrivedAtSystemEvent(Event):
    fleet: Entity
    system: Entity
