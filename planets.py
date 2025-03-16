import heapq
import math

class Ship:

    # We should have colonizer ships, fighters, and scouts (?)
    def __init__(self, ship_type, kinetics, phasers, hull, shield, ship_range, speed):
        self.ship_type = ship_type

        # This should be 0 for anything that isn't a fighter, since fighter vs.
        # scout/colonizer should be an instant win for the fighter
        self.kinetics = kinetics
        self.phasers = phasers
        self.hull = hull
        self.shield = shield

        # Should these be the same for all ships? It would make more sense for
        # scouts to have high range/speed, fighters have medium range/speed, and
        # colonizers to have high range but lower speed.
        self.range = ship_range
        self.speed = speed

        self.techs = {
            "kinetics": 0,
            "phasers": 0,
            "hull": 0,
            "shield": 0,

            "range": 1, # measured in... light-years?
            "speed": 0.001 # 0 = literally cannot move, 1 = c
        }

        # Roughly corresponds to what amount is contributed to each tech per
        # tick
        self.tech_focuses = {
            "kinetics": 0,
            "phasers": 0,
            "hull": 0,
            "shield": 0,
            "range": 0,
            "speed": 0
        }


class System:

    def __init__(self, system_id, x, y):
        self.system_id = system_id
        self.civ_id = 0

        self.x = x
        self.y = y

        self.year = 0
        self.event_queue = []


    def tick(self):
        self.year += 1

        while self.event_queue and self.event_queue[0][0] == self.year:
            _, message = heapq.heappop(self.event_queue)
            print(f"SYSTEM {self.system_id}, YEAR {self.year}: {message}")


    def broadcast_message(self, message, systems):
        print(f"Broadcasting message '{message}' from system {self.system_id} in local year {self.year}")

        for system in systems:

            # Don't broadcast to ourselves
            # TODO: or maybe we should? If we consume right after
            if system.system_id == self.system_id:
                continue

            # The distance to the other system (rounded up) is also the exact
            # amount of ticks that it'll take for the other system to receive
            # the message.
            dist = math.sqrt((self.x - system.x)**2 + (self.y - system.y)**2)
            future_time = system.year + math.ceil(dist)

            heapq.heappush(system.event_queue, (future_time, message))


s1 = System(0, 0, 0)
s2 = System(1, 3, 4)
s1.broadcast_message("HELLO FROM YEAR 0", [s1, s2])

for i in range(10):
    s1.tick()
    s2.tick()