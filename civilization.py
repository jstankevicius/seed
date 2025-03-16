
class Civilization:

    next_id = 0

    def __init__(self, home_system: System):
        self.id = Civilization.next_id
        Civilization.next_id += 1

        self.systems: set[System] = {home_system}
        home_system.ruling_civilization = self

        self.ship_range = 20

        self.reachable_systems = []
        self.adjacency_list: dict[System, list[System]] = {}
        self.calculate_adjacency_list()

    def calculate_adjacency_list(self) -> None:
        all_systems = System.registry
        for sys1 in all_systems:
            for sys2 in all_systems:
                if sys1 is sys2:
                    continue

                if sys1.distance_to(sys2) <= self.ship_range:
                    if sys1 not in self.adjacency_list:
                        self.adjacency_list[sys1] = []

                    self.adjacency_list[sys1].append(sys2)

    def calculate_reachable_systems(self) -> list[System]:

        # Will have been invalidated by System on ownership change
        if self.reachable_systems:
            return self.reachable_systems

        self.reachable_systems = [
            system
            for owned_system in self.systems
            for system in self.adjacency_list.get(owned_system, [])
            if system.ruling_civilization != self
        ]
        return self.reachable_systems

    def get_route_between_systems(
        self, source: System, target: System
    ) -> list[tuple[System, System]]:
        def heuristic(system: System) -> float:
            # Use Euclidean distance as the heuristic
            return system.distance_to(target)

        adjacency = self.adjacency_list
        dist = {system: float("inf") for system in systems}
        previous = {system: None for system in systems}
        dist[source] = 0

        heap = [(0 + heuristic(source), 0, source)]  # (priority, distance, system)

        while heap:
            _, current_dist, current = heappop(heap)
            if current == target:
                break
            if current_dist > dist[current]:
                continue
            for neighbor in adjacency[current]:
                weight = current_dist + 1  # Each hop has a cost of 1
                if weight < dist[neighbor]:
                    dist[neighbor] = weight
                    previous[neighbor] = current
                    heappush(heap, (weight + heuristic(neighbor), weight, neighbor))

        # Reconstruct the path (same as before)
        path_nodes = deque()
        curr = target
        while curr is not None:
            path_nodes.appendleft(curr)
            curr = previous[curr]

        path_nodes = list(path_nodes)
        edges = [(path_nodes[i], path_nodes[i + 1]) for i in range(len(path_nodes) - 1)]
        return edges

    def act(self) -> None:
        # Pick a home system at random
        if not self.systems:
            return

        source: System = random.choice(list(self.systems))
        reachable_systems = self.calculate_reachable_systems()

        if not reachable_systems:
            return

        target = random.choice(reachable_systems)
        if source == target:
            print(f"Warning: Source {source} is the same as target {target}!")
            return

        # Send half of our ships to some reachable system that isn't ours
        path = self.get_route_between_systems(source, target)
        _, next_system = path[0]

        # Divide fleet in half
        if not source.orbiting_fleets:
            print(f"Source system {source} has no available ships.")
            return

        source_fleet = source.orbiting_fleets[0]
        new_fleet_size = source_fleet.size // 2
        source_fleet.size -= new_fleet_size

        # Send to first system in the path
        # speed = distance / time -> time = distance / speed
        fleet = Fleet(self, new_fleet_size)
        arrival_tick = source.tick + int(source.distance_to(next_system) / fleet.speed)

        heappush(next_system.fleet_queue, (arrival_tick, fleet, path))