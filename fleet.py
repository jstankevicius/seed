
class Fleet:
    def __init__(self, civilization, size):
        self.civilization = civilization
        self.size = size

        # TODO
        self.speed = 0.25

    def __lt__(self, other: Fleet) -> bool:
        # Compare fleets based on size as a default comparison
        return self.civilization.id < other.civilization.id