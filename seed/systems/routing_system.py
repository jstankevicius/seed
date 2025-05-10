from heapq import heappush, heappop
from functools import cache
from typing import Generator
from collections import deque
import math

from seed.systems.base import System, handle
from seed.world_state import WorldState
from seed.common.base_types import (
    Entity,
    SystemComponent,
    CivilizationComponent,
    FleetComponent,
)
from seed.common.events import (
    EventBus,
    SystemOwnerChangedEvent,
    FleetStartedRouteToSystemEvent,
)


class RoutingSystem(System):
    """System for pathfinding and route management between star systems."""

    def __init__(self, w: WorldState, event_bus: EventBus):
        super().__init__(w, event_bus)
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

        # HACK: Warm up cache for each civ's reachable systems. Requires that
        # RoutingSystem runs before CivilizationSystem
        for e_civ, _ in self.w.get_components(CivilizationComponent):
            self.get_civ_reachable_systems(e_civ)

    def update(self) -> None:
        pass

    @cache
    def get_distance(self, e_sys1: Entity, e_sys2: Entity) -> float:
        """Return the distance between two systems."""
        x1, y1 = self.w.get_entity_component(e_sys1, SystemComponent).position
        x2, y2 = self.w.get_entity_component(e_sys2, SystemComponent).position
        return math.hypot(x1 - x2, y1 - y2)

    @cache
    def get_reachable_neighbors(
        self, e_sys: Entity, ship_range: int
    ) -> Generator[tuple[Entity, SystemComponent], None, None]:
        """Given a ship range and a system, return the systems that are immediately
        reachable from the source system.
        """
        computed = set()
        for e_sys_other, sys_component in self.systems:
            if (
                self.get_distance(e_sys, e_sys_other) <= ship_range
                and e_sys_other not in computed
            ):
                computed.add(e_sys_other)
                yield (e_sys_other, sys_component)

    def get_civ_reachable_systems(self, civ_entity: Entity) -> list[Entity]:
        civ = self.w.get_entity_component(civ_entity, CivilizationComponent)

        # Cache is still valid
        if civ.reachable_systems:
            return civ.reachable_systems

        # Cache has been invalidated
        civ.reachable_systems = [
            entity
            for owned_system in civ.owned_systems
            for entity, system in self.get_reachable_neighbors(
                owned_system, civ.ship_range
            )
            if system.owning_civ != civ_entity
        ]
        return civ.reachable_systems

    def get_route(self, fleet, source, target):
        def heuristic(system: Entity) -> float:
            return self.get_distance(system, target)

        e_civ = self.w.get_entity_component(fleet, FleetComponent).owning_civ
        civ = self.w.get_entity_component(e_civ, CivilizationComponent)
        dist = {entity: float("inf") for entity, _ in self.systems}
        previous = {entity: None for entity, _ in self.systems}
        dist[source] = 0

        heap = [(0 + heuristic(source), 0, source)]  # (priority, distance, system)

        while heap:
            _, current_dist, current = heappop(heap)
            if current == target:
                break
            if current_dist > dist[current]:
                continue
            for neighbor in self.get_reachable_neighbors(current, civ.ship_range):
                weight = current_dist + self.get_distance(current, neighbor)
                if weight < dist[neighbor]:
                    dist[neighbor] = weight
                    previous[neighbor] = current
                    heappush(heap, (weight + heuristic(neighbor), weight, neighbor))

        # Reconstruct the path
        path_nodes = deque()
        curr = target
        while curr is not None:
            path_nodes.appendleft(curr)
            curr = previous[curr]

        path_nodes = list(path_nodes)
        edges = [(path_nodes[i], path_nodes[i + 1]) for i in range(len(path_nodes) - 1)]
        return edges

    # Event handlers
    @handle(SystemOwnerChangedEvent, priority=-100)
    def on_system_owner_changed(self, event: SystemOwnerChangedEvent) -> None:
        system = event.system
        old_owner = event.old_owner
        new_owner = event.new_owner

        # Invalidate caches for both the old owner and the new, since both of their
        # owned system sets changed.
        if old_owner:
            old_owner_civ = self.w.get_entity_component(
                old_owner, CivilizationComponent
            )
            old_owner_civ.reachable_systems = self.get_civ_reachable_systems(old_owner)

        if new_owner:
            new_owner_civ = self.w.get_entity_component(
                new_owner, CivilizationComponent
            )
            new_owner_civ.reachable_systems = self.get_civ_reachable_systems(new_owner)

    @handle(FleetStartedRouteToSystemEvent)
    def on_fleet_started_route(self, event: FleetStartedRouteToSystemEvent) -> None:
        self.get_route(event.fleet, event.source, event.target)
