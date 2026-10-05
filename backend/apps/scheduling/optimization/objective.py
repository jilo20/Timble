import pyomo.environ as pyo


def add_objective(model, scenario):
    """Minimize sum_(o,m,f,r,d,p) (capacity[r]-students[o]) x[o,m,f,r,d,p].
    Waste is counted per scheduled meeting, not per occupied period.
    """
    model.room_waste = pyo.Objective(
        expr=sum(
            (scenario.rooms[r - 1]["capacity"] - scenario.offerings[o - 1]["students"])
            * model.x[o, m, f, r, d, p]
            for o, m, f, r, d, p in model.C
        ),
        sense=pyo.minimize,
    )
