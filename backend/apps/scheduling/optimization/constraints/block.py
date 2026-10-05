import pyomo.environ as pyo


def add_block(model, scenario, groups):
    """For each (block,d,p), sum of all starts covering p <= 1."""
    model.block_collision = pyo.ConstraintList()
    for keys in groups["block"].values():
        model.block_collision.add(sum(model.x[k] for k in keys) <= 1)
