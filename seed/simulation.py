import random
import math

from seed.world_state import WorldState
from seed.common.base_types import *
from seed.systems.system import System, SystemSystem, RoutingSystem, CivilizationSystem

NUM_SYSTEMS = 200
NUM_STARTING_CIVILIZATIONS = 4


def generate_galaxy(
    num_systems: int = 200,
    num_arms: int = 4,
    arm_spread: float = 0.3,
    radius: int = 30,
) -> list[tuple[float, float]]:

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
        yield (x, y)


class SimulationManager:
    def __init__(self):
        self.world_state = WorldState()
        self.systems = []

    def add_system(self, system_type: type[System]) -> None:
        self.systems.append(system_type(self.world_state))

    def initialize(self):
        # Generate galaxy
        systems = [
            self.world_state.add_entity(
                SystemComponent(owning_civ=None, position=(x, y))
            )
            for x, y in generate_galaxy(NUM_SYSTEMS)
        ]

        # Populate some initial systems
        civs = [
            self.world_state.add_entity(CivilizationComponent(owned_systems=[sys]))
            for sys in random.sample(systems, NUM_STARTING_CIVILIZATIONS)
        ]
        print(len(systems))
        print(len(civs))

    # Maybe this should yield snapshots of the sim?
    def run_loop(self, num_steps: int) -> None:
        for system in self.systems:
            system.start()

        for tick in range(num_steps):
            for system in self.systems:
                system.update()

            self.world_state.dispatch_events()


if __name__ == "__main__":
    s = SimulationManager()
    s.initialize()
    s.add_system(SystemSystem)
    s.add_system(RoutingSystem)
    s.add_system(CivilizationSystem)
    s.run_loop(1000)
