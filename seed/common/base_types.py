from dataclasses import dataclass, field
from collections import deque

"""
Access patterns:
Really, everything (or nearly everything) relates to systems in some way.
How do we do iterations over the game state in such a way that we minimize
the number of iterations?
Options:
A) 1. go over each civ and its owned systems. build ships, route ships, etc.
        Or go over each civ and... all systems. Then switch based on system ownership:
            1. owned systems
            2. systems owned by someone else
            3. uncolonized systems


Defer things when possible. We should have a loop of update() -> make_decisions().
Should we keep the event based system?

What happens if there is a system owner change and different modules need to react to
it?
e.g. update reachable systems, calculate diplomatic scores

   civilizations
systems      fleets

characters?

"""


@dataclass(slots=True)
class System:
    idx: int

    # Access to this won't be needed very often, so we can afford the extra indirection
    owning_civ_index: int | None
    position: tuple[float, float]

    parked_fleets: list[int]


@dataclass
class Civilization:
    idx: int

    owned_systems: list[System] = field(default_factory=lambda: [])
    reachable_systems: list[Entity] | None = None
    ship_range: int = 8


@dataclass
class Fleet:
    idx: int

    owning_civ: int | None
    size: int
    parked_system: int | None


@dataclass(slots=True)
class Simulation:
    systems: list[System] = field(default_factory=lambda: [])
    civilizations: list[Civilization] = field(default_factory=lambda: [])

    fleets: list[Fleet] = field(default_factory=lambda: [])
    fleet_queue = deque()
