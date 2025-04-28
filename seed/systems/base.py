from abc import ABC
import inspect

from seed.world_state import WorldState
from seed.common.events import Event, EventBus


def handle(event_type: type[Event], priority: int = 0) -> None:
    """Decorator to mark a method as an event handler."""

    def wrapper(func: callable):
        func._handled_event_type = event_type
        func._event_priority = priority
        return func

    return wrapper


class System(ABC):
    """Base class for all systems in the simulation."""

    def __init__(self, w: WorldState, event_bus: EventBus):
        self.w = w
        self.event_bus = event_bus
        self._register_event_handlers()

    def start(self) -> None:
        """Initialize the system. Called once before the simulation starts."""
        pass

    def update(self) -> None:
        """Update the system state. Called once per tick."""
        pass

    def _register_event_handlers(self) -> None:
        """Register all methods decorated with @handle as event handlers."""
        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, "_handled_event_type"):
                priority = getattr(method, "_event_priority")
                self.event_bus.subscribe(method._handled_event_type, method, priority)
