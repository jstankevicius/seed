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
from system import System
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
        self.tick = 0

        self.systems = []
        self.civilizations = []

        # Queue
        self.fleets = []

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
            self.systems.append(System(x, y))

        # Place (starting) civilizations
        home_systems = random.sample(self.systems, num_starting_civilizations)
        self.civilizations = [Civilization(system) for system in home_systems]

    def process_civilization(self, civilization: Civilization) -> None:
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
