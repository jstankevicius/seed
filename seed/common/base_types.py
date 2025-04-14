from dataclasses import dataclass, field

# A basic entity
class Entity:
    _next_id: int = 0

    def __init__(self):
        self.id = Entity._next_id
        Entity._next_id += 1

    def __hash__(self):
        return self.id


# Components
class Component:
    pass


@dataclass
class SystemComponent:
    owning_civ: Entity | None

    # Should this be its own component? Systems and fleets have positions, but
    # fleet positions are calculated purely for the purposes of visualization.
    position: tuple[float, float]

    num_ships: int = 0


@dataclass
class CivilizationComponent(Component):
    owned_systems: list[Entity] = field(default_factory=lambda: [])
    reachable_systems: list[Entity] = field(default_factory=lambda: [])


@dataclass
class FleetComponent(Component):
    owning_civ: Entity | None

