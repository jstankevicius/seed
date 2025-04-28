import random

from seed.systems.base import System
from seed.world_state import WorldState
from seed.common.base_types import CivilizationComponent, FleetComponent
from seed.common.events import EventBus, FleetStartedRouteToSystemEvent


class CivilizationSystem(System):
    """System for managing civilization behaviors and decision-making."""

    def __init__(self, w: WorldState, event_bus: EventBus):
        super().__init__(w, event_bus)
        self.civs = []

    def start(self) -> None:
        # TODO: Recalculate on some NewCivilizationAddedEvent, maybe.
        self.civs = [
            (entity, civ)
            for entity, (civ,) in self.w.get_components(CivilizationComponent)
        ]

    def update(self) -> None:
        for entity, civ in self.civs:
            # Pick a random owned system
            if not civ.owned_systems:
                print(f"Civilization {civ} has no owned systems!")
                continue

            source = random.choice(civ.owned_systems)

            # Pick a random reachable system
            reachable_systems = civ.reachable_systems
            if not reachable_systems:
                print(f"Civilization {civ} has no reachable systems")
                continue

            target = random.choice(reachable_systems)
