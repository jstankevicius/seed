
class Species:

    _next_id = 0

    def __init__(self, name: str):
        self.name = name
        self.id = Species._next_id
        Species._next_id += 1