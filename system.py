
class System:

    def __init__(self, system_id: int, x: float, y: float):
        self.id = system_id

        # It is expected that all instances of System have the same tick value.
        self.tick = 0

        self.pops: list[Pop] = []
        self.coordinates = (x, y)
        self.resources = 0
        self.infrastructure_level = 1
        self.civ_id: int | None
        self.orbiting_fleets: list[Fleet] = []


    def process_arriving_fleets(self) -> None:

        # Ingest all fleets that are arriving this tick
        while self.fleet_queue and self.fleet_queue[0][0] == self.tick:
            _, fleet, path = heappop(self.fleet_queue)

            if not path:
                print(f"Warning: Fleet {fleet} has an empty path")
                continue

            _, target_system = path.pop(0)
            if self != target_system:
                print(
                    f"Warning: Fleet {fleet} arrived at {self}, but its target system was {target_system}!"
                )
                continue

            # If this fleet isn't ours, it's attacking. Its final destination does not
            # matter.
            if (
                self.ruling_civilization is not None
                and fleet.civilization != self.ruling_civilization
            ):
                # Check if the attacking civilization has any systems left
                if not fleet.civilization.systems:
                    print(
                        f"Fleet from {fleet.civilization} cannot attack as it has no systems left."
                    )
                    continue

                # Check if there are defending fleets
                defending_fleets = [
                    fleet
                    for fleet in self.orbiting_fleets
                    if fleet.civilization == self.ruling_civilization
                ]

                if defending_fleets:
                    # Engage in battle
                    defending_fleet = defending_fleets[0]
                    if fleet.size > defending_fleet.size:
                        # Attacker wins, reduce attacking fleet size
                        fleet.size -= defending_fleet.size
                        self.orbiting_fleets.remove(defending_fleet)
                        print(
                            f"{self} has been attacked and the defending fleet was destroyed!"
                        )
                        # Set the attacker as the new ruling civilization
                        self.set_ruling_civilization(fleet.civilization)
                    elif fleet.size < defending_fleet.size:
                        # Defender wins, reduce defending fleet size
                        defending_fleet.size -= fleet.size
                        print(f"{self} successfully defended against an attack!")
                    else:
                        # Both fleets destroy each other
                        self.orbiting_fleets.remove(defending_fleet)
                        print(
                            f"{self} experienced a battle where both fleets were destroyed!"
                        )
                else:
                    # No defending fleets, attacker takes over
                    self.orbiting_fleets.append(fleet)
                    print(
                        f"{self} is being attacked by a foreign fleet and has no defense!"
                    )
                    # Set the attacker as the new ruling civilization
                    self.set_ruling_civilization(fleet.civilization)
                continue

            # If this fleet does belong to us, it's either supposed to stop here or move
            # on to another system.
            if len(path) > 0:
                _, next_system = path[0]

                # speed = distance / time -> time = distance / speed
                arrival_tick = self.tick + int(
                    self.distance_to(next_system) / fleet.speed
                )
                heappush(next_system.fleet_queue, (arrival_tick, fleet, path))
            else:
                # final destination. hang out here.
                self.orbiting_fleets.append(fleet)

                if self.ruling_civilization is None:
                    self.set_ruling_civilization(fleet.civilization)

    def process_tick(self) -> None:
        self.process_rebels()
        self.process_arriving_fleets()
        self.build_ships()
        self.merge_fleets()
        self.tick += 1

    def __repr__(self) -> str:
        return f"System({self.id})"

    def __lt__(self, other) -> bool:
        return self.id < other.id


