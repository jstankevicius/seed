from seed.common.base_types import Entity, Component
from seed.common.events import Event, EventBus

from collections import defaultdict
from dataclasses import dataclass


class WorldState:

    # Helper class
    class EntityToComponentMap:
        def __init__(self):
            self.entity_set: set[Entity] = set()
            self.entity_map: dict[Entity, Component] = dict()

    def __init__(self):
        # self._components: dict[type(Component), EntityToComponentMap]
        self._components = defaultdict(self.EntityToComponentMap)
        self._event_bus = EventBus()

    def subscribe_event(self, event_type: type[Event], callback: callable) -> None:
        self._event_bus.subscribe(event_type, callback)

    def publish_event(self, event: Event) -> None:
        self._event_bus.publish(event)

    def dispatch_events(self) -> None:
        self._event_bus.dispatch()

    def add_entity(self, *components) -> Entity:
        new_entity = Entity()

        for comp_object in components:
            comp_type = type(comp_object)
            self._components[comp_type].entity_map[new_entity] = comp_object
            self._components[comp_type].entity_set.add(new_entity)

        return new_entity

    def add_to_entity(self, entity: Entity, **components) -> Entity:
        for comp_type, comp_object in components.items():
            self._components[comp_type].entity_map[entity] = comp_object

        return entity

    def remove_entity(self, entity: Entity) -> None:
        for comp_type in self._components.items():
            del self._components[comp_type][entity]
            self._components[comp_type].remove(entity)

    def remove_from_entity(self, entity: Entity, **components) -> None:
        for comp_type, comp_object in components.items():
            del self._components[comp_type][entity]

    def get_entity_component(self, entity: Entity, component_type):
        return self._components[component_type].entity_map[entity]

    def get_components(self, *component_types):
        # Return an entity and all the components belonging to that entity. Components
        # are returned in the order specified in get_components.
        entities = set.intersection(
            *(self._components[t].entity_set for t in component_types)
        )

        for entity in entities:
            yield entity, tuple(
                self._components[t].entity_map[entity] for t in component_types
            )
