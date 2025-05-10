import random

from seed.systems.base import System
from seed.world_state import WorldState
from seed.common.base_types import (
    CivilizationComponent,
    FleetComponent,
)
from seed.common.events import EventBus, FleetStartedRouteToSystemEvent


class CivilizationSystem(System):
    """System for managing civilization behaviors and decision-making."""

    def __init__(self, w: WorldState, event_bus: EventBus):
        super().__init__(w, event_bus)
        self.civs = []

    def start(self) -> None:
        # TODO: Recalculate on some NewCivilizationAddedEvent, maybe.

        self.civs = [(e, c) for e, (c,) in self.w.get_components(CivilizationComponent)]

        if not self.civs:
            raise RuntimeError("Civ list is empty!")

    def update(self) -> None:
        for e_civ, civ in self.civs:
            # Pick a random owned system
            if not civ.owned_systems:
                print(f"Civilization {civ} has no owned systems!")
                continue

            # Pick a random parked fleet
            parked_fleets = [
                (e_fleet, fleet)
                for e_fleet, (fleet,) in self.w.get_components(FleetComponent)
                if fleet.owning_civ == e_civ and fleet.parked_system
            ]

            print(f"There are {len(parked_fleets)} parked fleets.")
            e_fleet, fleet = random.choice(parked_fleets)

            # Pick a random reachable system
            reachable_systems = civ.reachable_systems
            if not reachable_systems:
                print(f"Civilization {civ} has no reachable systems")
                continue

            target = random.choice(reachable_systems)

            # Send the entire fleet to target
            self.event_bus.publish(
                FleetStartedRouteToSystemEvent(
                    fleet=e_fleet, source=fleet.parked_system, target=target
                )
            )

            # Mark it as no longer parked
            fleet.parked_system = None
