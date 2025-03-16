from simulation import Civilization, System, Fleet
from typing import List, Tuple


class Snapshot:
    def __init__(
        self,
        tick: int,
        systems: List[System],
        civilization_colors: dict[Civilization, str],
    ):
        self.tick = tick
        self.colors: List[str] = []
        self.fleet_positions: List[Tuple[float, float, str]] = []

        self._create_snapshot(systems, civilization_colors)

    def _create_snapshot(
        self, systems: List[System], civilization_colors: dict[Civilization, str]
    ) -> None:
        for system in systems:
            # Assign a color based on the ruling civilization
            if system.ruling_civilization:
                color = civilization_colors[system.ruling_civilization]
            else:
                color = "gray"  # Gray for uninhabited systems
            self.colors.append(color)

            # Add fleets as smaller dots
            for fleet in system.orbiting_fleets:
                fleet_color = civilization_colors[fleet.civilization]
                self.fleet_positions.append((*system.coordinates, fleet_color))

            # Add traveling fleets
            for arrival_tick, fleet, path in system.fleet_queue:
                if path:
                    # Interpolate fleet position along the path
                    start_system, end_system = path[0]
                    if fleet.speed == 0:
                        continue

                    # Calculate progress based on the current tick
                    total_distance = start_system.distance_to(end_system)
                    travel_time = total_distance / fleet.speed
                    progress = (
                        system.tick - (arrival_tick - travel_time)
                    ) / travel_time

                    # Ensure progress is between 0 and 1
                    progress = max(0, min(1, progress))

                    # Interpolate position
                    x = start_system.coordinates[0] + progress * (
                        end_system.coordinates[0] - start_system.coordinates[0]
                    )
                    y = start_system.coordinates[1] + progress * (
                        end_system.coordinates[1] - start_system.coordinates[1]
                    )
                    fleet_color = civilization_colors[fleet.civilization]
                    self.fleet_positions.append((x, y, fleet_color))
