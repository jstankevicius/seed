from abc import ABC
from collections import deque
from dataclasses import dataclass
from seed.common.base_types import *

from heapq import heappush, heappop


@dataclass
class Event(ABC):
    pass


class EventBus:
    def __init__(self):
        # Event -> list[(priority, callable)]
        self._listeners = {}
        self._queue = deque()
        self._scheduled_events = []
        self.current_tick = 0

    def subscribe(
        self, event_type: type[Event], callback: callable, priority: int = 0
    ) -> None:
        """Subscribe to an event with a priority (lower values fire first)"""
        self._listeners.setdefault(event_type, []).append((priority, callback))
        self._listeners[event_type].sort(key=lambda x: x[0])

    def publish(self, event: Event) -> None:
        self._queue.append(event)

    def schedule(self, future_tick: int, event: Event) -> None:
        heappush(self._scheduled_events, (future_tick, event))

    def dispatch(self) -> None:
        while self._queue:
            event = self._queue.popleft()
            # Callbacks are already sorted by priority
            for _, callback in self._listeners.get(type(event), []):
                callback(event)

    def advance_time(self) -> None:
        self.current_tick += 1

        while (
            self._scheduled_events and self._scheduled_events[0][0] <= self.current_tick
        ):
            _, event = heappop(self._scheduled_events)
            self.publish(event)


@dataclass
class TinkerTaskStartedEvent(Event):
    foo: Entity


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
