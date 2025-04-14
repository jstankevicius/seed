from abc import ABC

from seed.world_state import WorldState
from seed.common.base_types import *
from seed.common.events import *

import random
import math


class System(ABC):
    def __init__(self, w: WorldState):
        self.w = w

    def start(self) -> None:
        raise NotImplementedError(f"{self.__name__} has not implemented start()!")

    def update(self) -> None:
        raise NotImplementedError(f"{self.__name__} has not implemented update()!")


# Yes it's a weird name. No I'm not changing it. System can refer to both the
# abstract object responsible for managing components and to a star system.
class SystemSystem(System):
    def __init__(self, w: WorldState):
        super().__init__(w)
        self.systems = []

    def start(self) -> None:
        # The number of system entities won't change, so there's no point in
        # querying for the same list over and over again.
        self.systems = [
            (entity, sys) for entity, (sys,) in self.w.get_components(SystemComponent)
        ]

    def update(self) -> None:
        for entity, sys in self.systems:
            if sys.owning_civ is not None:
                sys.num_ships += 1
                print(f"{sys} has {sys.num_ships} ships!")


class RoutingSystem(System):
    def __init__(self, w: WorldState):
        super().__init__(w)
        self.systems = []
        self.fleet_queue = []

        # Caches
        self.systems_reachable_by_hop = {}
        self.system_distances = {}

    def start(self) -> None:
        # The number of system entities won't change, so there's no point in
        # querying for the same list over and over again.
        self.systems = [
            (entity, sys) for entity, (sys,) in self.w.get_components(SystemComponent)
        ]

        # Pre-calculate system distances
        for entity1, sys1 in self.systems:
            self.system_distances[entity1] = {}
            for entity2, sys2 in self.systems:
                x1, y1 = sys1.position
                x2, y2 = sys2.position
                dist = math.hypot(x1 - x2, y1 - y2)
                self.system_distances[entity1][entity2] = dist

        # Subscribe to events
        self.w.subscribe_event(SystemOwnerChangedEvent, self.on_system_owner_changed_event)

    def update(self) -> None:
        pass

    def get_distance(self, sys_entity1, sys_entity2) -> float:
        return self.system_distances[sys_entity1][sys_entity2]

    def get_route(self, civ, source, target):
        pass

    def get_civ_reachable_systems(self, civ_entity: Entity) -> list[Entity]:
        civ = self.w.get_entity_component(civ_entity, CivilizationComponent)

        # Cache is still valid
        if civ.reachable_systems:
            return civ.reachable_systems

        # Cache has been invalidated
        civ.reachable_systems = [
            system
            for owned_system in civ.owned_systems
            for system in self.systems_reachable_by_hop[owned_system]
            if system.owning_civ != civ_entity
        ]
        return civ.reachable_systems

    # Event handlers
    def on_system_owner_changed_event(event: SystemOwnerChangedEvent) -> None:
        system = event.system
        old_owner = event.old_owner
        new_owner = event.new_owner

class CivilizationSystem(System):
    def __init__(self, w: WorldState):
        super().__init__(w)
        self.civs = []

    def start(self) -> None:
        # TODO: Recalculate on some NewCivilizationAddedEvent, maybe.
        self.civs = [
            (entity, civ) for entity, (civ,) in self.w.get_components(CivilizationComponent)
        ]

    def update(self) -> None:
        for entity, civ in self.civs:
            # Pick a random owned system
            source = random.choice(civ.owned_systems)

            # Pick a random reachable system
            if civ.reachable_systems:
                target = random.choice(civ.reachable_systems)
