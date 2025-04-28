from seed.world_state import WorldState
from seed.common.events import EventBus, SystemOwnerChangedEvent
from seed.common.base_types import *


def transfer_system_ownership(
    w: WorldState, event_bus: EventBus, system: Entity, new_owner: Entity
) -> None:
    sys_comp = w.get_entity_component(system, SystemComponent)
    old_owner = sys_comp.owning_civ

    # Update both components
    if old_owner:
        old_civ = w.get_entity_component(old_owner, CivilizationComponent)
        old_civ.owned_systems.remove(system)

    if new_owner:
        new_civ = w.get_entity_component(new_owner, CivilizationComponent)
        new_civ.owned_systems.append(system)

    sys_comp.owning_civ = new_owner

    event_bus.publish(
        SystemOwnerChangedEvent(system=system, old_owner=old_owner, new_owner=new_owner)
    )
