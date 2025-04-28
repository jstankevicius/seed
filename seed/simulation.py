import os
import random
import math

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Generator

from seed.world_state import WorldState
from seed.common.base_types import *
from seed.common.events import Event, EventBus, TinkerTaskStartedEvent
from seed.systems import System, SystemSystem, RoutingSystem, CivilizationSystem

import seed.common.utils as utils

import atomics

NUM_SYSTEMS = 200
NUM_STARTING_CIVILIZATIONS = 4


def generate_galaxy(
    num_systems: int = 200,
    num_arms: int = 4,
    arm_spread: float = 0.3,
    radius: int = 30,
) -> Generator[tuple[float, float], None, None]:

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


class Simulation:

    def __init__(self):
        self.world_state = WorldState()
        self.event_bus = EventBus()
        self.systems = []

    def add_system(self, system_type: type[System]) -> None:
        self.systems.append(system_type(self.world_state, self.event_bus))


class TinkerTask(Simulation):

    def __init__(self):
        super().__init__()

        # Set by self, read by parent simulation
        self._iterations = atomics.atomic(4, atype=atomics.INT)

    @property
    def iterations(self):
        return self._iterations

    @iterations.getter
    def iterations(self):
        return self._iterations.load()

    @iterations.setter
    def iterations(self, value):
        self._iterations.store(value)


class MainSimulation(Simulation):

    def __init__(self):
        super().__init__()

        self.tick = 0

        self.executor = ThreadPoolExecutor(max_workers=os.process_cpu_count())
        self.running_tasks: list[tuple[Simulation, Future]] = []

        # XXX: Listen from downstream whenever a system tells us that we need to spawn
        # a new sub-simulation.
        self.event_bus.subscribe(TinkerTaskStartedEvent, self.spawn_tinker_task)

    def initialize(self):
        # Generate galaxy
        systems = [
            self.world_state.add_entity(
                SystemComponent(owning_civ=None, position=(x, y))
            )
            for x, y in generate_galaxy(NUM_SYSTEMS)
        ]

        # Populate some initial systems
        starting_systems = random.sample(systems, NUM_STARTING_CIVILIZATIONS)
        civs = []

        for system in starting_systems:
            civ = self.world_state.add_entity(CivilizationComponent())
            civs.append(civ)

            utils.transfer_system_ownership(
                self.world_state, self.event_bus, system, civ
            )

        print(len(systems))
        print(len(civs))

    # Maybe this should yield snapshots of the sim?
    def run_loop(self, n_ticks: int) -> None:
        print("Running simulation")
        for system in self.systems:
            print("Started system", system)
            system.start()

        for _ in range(n_ticks):
            for system in self.systems:
                system.update()

            self.event_bus.dispatch()

            # Adjust time
            self.event_bus.advance_time()

    # HACK:
    def spawn_tinker_task(self, event: TinkerTaskStartedEvent) -> None:
        print("Spawned a tinker task")
        t = TinkerTask()
        t.iterations += 1
        print(t.iterations)


if __name__ == "__main__":
    s = MainSimulation()
    s.initialize()
    s.add_system(SystemSystem)
    s.add_system(RoutingSystem)
    s.add_system(CivilizationSystem)
    s.run_loop(1000)
