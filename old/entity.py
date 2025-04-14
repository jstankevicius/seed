class Entity:
    """An identity represented with an ID."""

    _next_id = 0

    def __init__(self):
        self.id = Entity._next_id
        Entity._next_id += 1
