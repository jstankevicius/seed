from __future__ import annotations

import math
import random
from collections import deque
from heapq import heappop, heappush
from typing import TypeAlias

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.widgets import Slider

from civilization import Civilization
from species import Species
from systems.system import System
from fleet import Fleet

# TODO:
# Pop mechanics
# Unrest mechanics
# Diplomacy? Truces/wars/peace deals
# Better invasion planning. Build up fleets on borders, pick weakest point.


class RebelGroup:

    def __init__(self):
        self.origin_pop = None
        self.size = 0

        # If this rebel group wins, this will be the civilization the system joins
        self.civilization = None
        self.leaders = []

    def rebel_weight(self) -> float:
        raw_weight = (1 - self.origin_pop.happiness) * self.origin_pop.size

        # Truncate down to 0 if below certain value
        return raw_weight if raw_weight > 0.2 else 0


class Simulation:

    def __init__(self):
        # Time unit
        self.tick = 0

        # Lists to iterate over
        self.systems = []
        self.civilizations = []

        # Fleet queue
        self.fleets = []

        # Precomputed values
        self.system_distances = []
        self.systems_reachable_by_hop = {}  # int (hop range) -> dict[System, list[System]]

    def generate_galaxy(
        self,
        num_starting_civilizations: int,
        num_systems: int = 200,
        num_arms: int = 4,
        arm_spread: float = 0.3,
        radius: int = 30,
    ) -> None:

        # Generate (star) systems
        for _ in range(num_systems):
            # Random distance from the center. Maybe have an actual distribution the
            # distance follows instead of just uniform?
            r = radius * random.random()
            arm = random.randrange(num_arms)
            base_angle = (arm * (2 * math.pi / num_arms)) + (r / radius * 2 * math.pi)
            angle = base_angle + random.uniform(-arm_spread, arm_spread)
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            self.systems.append(System(len(self.systems), x, y))

        # Precompute distances between systems
        for i in range(num_systems):
            self.system_distances.append([])
            for j in range(num_systems):
                x1, y1 = self.systems[i].coordinates
                x2, y2 = self.systems[j].coordinates
                dist = math.hypot(x1 - x2, y1 - y2)
                self.system_distances[i].append(dist)

        # Place (starting) civilizations
        home_systems = random.sample(self.systems, num_starting_civilizations)
        self.civilizations = [
            Civilization(len(self.civilizations), system) for system in home_systems
        ]

    def set_system_civ_id(self, sys: System, civ: Civilization | None) -> None:
        if sys.civ_id:
            self.civilizations[sys.civ_id].reachable_systems = []  # Invalidate cache
            self.civilizations[sys.civ_id].systems.remove(sys.civ_id)

        if civ:
            sys.civ_id = civ.id
            self.civilizations[civ.id].reachable_systems = []  # Invalidate cache
            self.civilizations[civ.id].systems.add(sys.id)

    def system_build_ships(self, sys: System) -> None:
        if not sys.civ_id:
            return

        if not sys.orbiting_fleets:
            sys.orbiting_fleets.append(Fleet(sys.civ_id, 1))
        else:
            sys.orbiting_fleets[0].size += sys.infrastructure_level

    def system_merge_fleets(self, sys: System) -> None:
        merged_fleets = {}
        for fleet in sys.orbiting_fleets:
            if fleet.civilization not in merged_fleets:
                merged_fleets[fleet.civilization] = fleet
            else:
                merged_fleets[fleet.civilization].size += fleet.size

        sys.orbiting_fleets = list(merged_fleets.values())

    def get_route(
        self, civ: Civilization, source: System, target: System
    ) -> list[tuple[System, System]]:

        def heuristic(system: System) -> float:
            return self.system_distances[system.id][target.id]

        adjacency = self.systems_reachable_by_hop[civ.ship_range]
        dist = {system: float("inf") for system in self.systems}
        previous = {system: None for system in self.systems}
        dist[source] = 0

        heap = [(0 + heuristic(source), 0, source)]  # (priority, distance, system)

        while heap:
            _, current_dist, current = heappop(heap)
            if current == target:
                break
            if current_dist > dist[current]:
                continue
            for neighbor in adjacency[current]:
                weight = current_dist + 1  # Each hop has a cost of 1
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

    def get_adjacency_list_for_ship_range(self, ship_range: int) -> list[list[System]]:
        # Use cached value if available
        if ship_range in self.systems_reachable_by_hop:
            return self.systems_reachable_by_hop[ship_range]

        self.systems_reachable_by_hop[ship_range] = {}

        for sys1 in self.systems:
            for sys2 in self.systems:
                if sys1 is sys2:
                    continue

                if self.system_distances[sys1.id][sys2.id] <= ship_range:
                    # Can change this to dict[System, list[System]]
                    self.systems_reachable_by_hop[ship_range][sys1].append(sys2)

        return self.systems_reachable_by_hop[ship_range]

    def get_civ_reachable_systems(self, civ: Civilization) -> list[System]:
        # Cache is still valid
        if civ.reachable_systems:
            return civ.reachable_systems

        # Cache has been invalidated (probably because civ.systems has changed)
        civ.reachable_systems = [
            system
            for owned_system in civ.systems
            for system in self.systems_reachable_by_hop[owned_system]
            if system.civ_id != civ.id
        ]
        return civ.reachable_systems

    def process_civilization(self, civ: Civilization) -> None:
        # Pick a home system at random
        if not civ.systems:
            return

        source: System = random.choice(list(self.systems))
        reachable_systems = self.get_civ_reachable_systems(civ)

        if not reachable_systems:
            return

        target = random.choice(reachable_systems)
        if source == target:
            print(f"Warning: Source {source} is the same as target {target}!")
            return

        # Send half of our ships to some reachable system that isn't ours
        path = self.get_route(civ, source, target)
        _, next_system = path[0]

        # Divide fleet in half
        if not source.orbiting_fleets:
            print(f"Source system {source} has no available ships.")
            return

        source_fleet = source.orbiting_fleets[0]
        new_fleet_size = source_fleet.size // 2
        source_fleet.size -= new_fleet_size

        # Send to first system in the path
        # speed = distance / time -> time = distance / speed
        fleet = Fleet(self, new_fleet_size)
        arrival_tick = source.tick + int(source.distance_to(next_system) / fleet.speed)

        heappush(next_system.fleet_queue, (arrival_tick, fleet, path))
        pass

    def process_system(self, system: System) -> None:
        pass

    def process_tick(self) -> None:
        for system in self.systems:
            self.process_system(system)

        for civ in self.civilizations:
            self.process_civilization(civ)

        self.tick += 1


if __name__ == "__main__":

    # civilization_colors = {
    #     civ: color
    #     for civ, color in zip(
    #         civilizations, ["#FF6F61", "#6BAED6", "#74C476", "#FDD835"]
    #     )
    # }

    # Simulate and capture snapshots every 10 ticks
    snapshots = []
    for tick in range(1000):
        if tick % 10 == 0:
            snapshots.append(Snapshot(tick, systems, civilization_colors))

        for civilization in civilizations:
            civilization.act()

        for system in systems:
            system.process_tick()

    # Prepare the initial plot
    fig, ax = plt.subplots(figsize=(8, 8))  # Make the figure square
    plt.subplots_adjust(bottom=0.25)

    x_vals, y_vals = zip(*[system.coordinates for system in systems])
    initial_colors = snapshots[0].colors
    scat = ax.scatter(x_vals, y_vals, c=initial_colors, s=50)
    ax.set_title(f"Galaxy Snapshot at tick {snapshots[0].tick}")
    ax.grid(True)

    # Ensure the axes have equal scaling
    ax.set_aspect("equal", adjustable="box")

    # Create a slider for timeline exploration
    ax_slider = plt.axes((0.15, 0.1, 0.7, 0.03))
    slider = Slider(
        ax=ax_slider, label="Tick", valmin=0, valmax=1000, valinit=0, valstep=10
    )

    def update(val: float) -> None:
        # Safely find the snapshot corresponding to the selected tick
        snapshot = next((snap for snap in snapshots if snap.tick == int(val)), None)

        if snapshot is None:
            print(f"No snapshot found for tick {int(val)}.")
            return

        # Update system colors
        scat.set_facecolors(snapshot.colors)

        # Clear and redraw fleet positions
        fleet_positions = snapshot.fleet_positions
        fleet_x, fleet_y, fleet_colors = (
            zip(*fleet_positions) if fleet_positions else ([], [], [])
        )

        # Remove previous fleet scatter plot before redrawing
        for coll in ax.collections[1:]:
            coll.remove()

        ax.scatter(fleet_x, fleet_y, c=fleet_colors, s=20, marker="x")

        ax.set_title(f"Galaxy Snapshot at tick {snapshot.tick}")
        fig.canvas.draw_idle()

    slider.on_changed(update)
    plt.show()
