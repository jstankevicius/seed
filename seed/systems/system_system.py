from seed.systems.base import System
from seed.world_state import WorldState
from seed.common.base_types import SystemComponent, FleetComponent
from seed.common.events import EventBus


class SystemSystem(System):
    """System for managing star systems and their properties."""

    def __init__(self, w: WorldState, event_bus: EventBus):
        super().__init__(w, event_bus)
        self.systems = []

    def start(self) -> None:
        # The number of system entities won't change, so there's no point in
        # querying for the same list over and over again.
        self.systems = [
            (entity, sys) for entity, (sys,) in self.w.get_components(SystemComponent)
        ]

    def build_ships(self) -> None:
        """Build fleets in every system at a rate of 1 per tick."""
        # First get all fleets that are already parked at some system.
        systems_with_fleets = set()
        for entity, (fleet,) in self.w.get_components(FleetComponent):
            if not fleet.parked_system:
                continue

            systems_with_fleets.add(fleet.parked_system)
            fleet.size += 1
            print(f"Built 1 ship at {fleet.parked_system}")

        # If there is a system with no fleets parked, create a fleet for that system.
        for entity, sys_component in self.systems:
            if sys_component.owning_civ and entity not in systems_with_fleets:
                self.w.add_entity(
                    FleetComponent(
                        owning_civ=sys_component.owning_civ,
                        size=1,
                        parked_system=entity,
                    ),
                )

    def update(self) -> None:
        self.build_ships()
