import os
import random
import math

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Generator
from dataclasses import dataclass
from collections import deque

import atomics

NUM_SYSTEMS = 200
NUM_STARTING_CIVILIZATIONS = 4

"""In the presence of light-speed lag, how do you communicate? How do
civilizations manage themselves across enormous distances?

What protocol is needed to ensure survival?

E.g. choosing when to rebel vs cooperate. How big can interstellar
civilizations get when they use particular messaging protocols, and every
system is decentralized?

Turns the simulation from civ-centric to system-centric. Now every civilization
is simply defined by a loose relational graph of systems. No need to hardcode
story elements or anything like that.

Systems:
    resource extraction
    where do resources go? To parent system?
        what would they be used for if they were given to the colony?
        why would a colony prefer that resources go to it instead of its parent?

    what do relation graphs look like?
    deep? i.e. each colony can have its own colonies
        what advantages does this bring, if any?
    flat? i.e. there is only one root -> colony connection. colonies cannot have their
    own colonies.

    what does a colony do when it's not receiving orders?
        building up its infrastructure?
        ...what do colonies do, in general?
        ...what do systems do?
            extract resources from their planet.
            more resources = better
            more resources = more infrastructure, more infrastructure = more ships,
            more expansion -> more resources
            a system wants to ensure
                1) survival
                2) given it survives, the maximum number of resources (and maximum
                   level of infrastructure) available to it.
"""


@dataclass(slots=True)
class System:
    idx: int
    position: tuple[float, float]
    parked_fleets: list[int]


@dataclass
class Fleet:
    idx: int

    owning_civ: int | None
    size: int
    parked_system: int | None


@dataclass(slots=True)
class Simulation:
    tick: int

    systems: list[System] = field(default_factory=lambda: [])
    civilizations: list[Civilization] = field(default_factory=lambda: [])

    fleets: list[Fleet] = field(default_factory=lambda: [])
    fleet_queue = deque()


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


def process_fleets(s: Simulation) -> None:
    """Process fleet arrivals.
    """
    while s.fleet_queue and s.fleet_queue[0][0] == s.tick:
        _, fleet, path = heappop(s.fleet_queue)


def process_battles(s: Simulation) -> None:
    pass

def run_simulation(n_iterations: int) -> None:
    sim = Simulation()

    for _ in range(n_iterations):
        process_fleets(s)
        process_battles(s)

        process_civs(s)


if __name__ == "__main__":
    s = Simulation()
