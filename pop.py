
class Pop:

    def __init__(self):
        self.species = None
        self.ideology = None
        self.size = 0
        self.growth_rate = 0.02
        self.happiness = 0

class Species:

    _next_id = 0

    def __init__(self, name: str):
        self.name = name
        self.id = Species._next_id
        Species._next_id += 1
