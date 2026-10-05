import pyomo.environ as pyo


def add_room(model, scenario, groups):
    """For each (room,d,p), sum of all starts covering p <= 1."""
    model.room_collision = pyo.ConstraintList()
    for keys in groups["room"].values():
        model.room_collision.add(sum(model.x[k] for k in keys) <= 1)
