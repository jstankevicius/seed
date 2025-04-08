from system import System

class Civilization:

    def __init__(self, civ_id: int, home_system: System):
        self.systems: set[System] = {home_system}
        home_system.ruling_civilization = self
        self.id = civ_id

        self.ship_range = 20

        self.reachable_systems = []
        self.adjacency_list: dict[System, list[System]] = {}
        self.calculate_adjacency_list()

    def calculate_adjacency_list(self) -> None:
        for sys1 in all_systems:
            for sys2 in all_systems:
                if sys1 is sys2:
                    continue

                if sys1.distance_to(sys2) <= self.ship_range:
                    if sys1 not in self.adjacency_list:
                        self.adjacency_list[sys1] = []

                    self.adjacency_list[sys1].append(sys2)