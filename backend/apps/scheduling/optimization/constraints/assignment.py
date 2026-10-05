import pyomo.environ as pyo


def add_assignment(model, scenario, groups):
    """For each (o,m), sum(f,r,d,p) x[o,m,f,r,d,p] = 1.
    Link every meeting to the same faculty: sum(r,d,p) x[o,m,f,r,d,p] = y[o,f].
    """
    model.assignment = pyo.ConstraintList()
    model.faculty_link = pyo.ConstraintList()
    for keys in groups["meeting"].values():
        model.assignment.add(sum(model.x[k] for k in keys) == 1)
    for oi, fi in model.E:
        for meeting in range(1, scenario.offerings[oi - 1]["meetings"] + 1):
            model.faculty_link.add(
                sum((model.x[k] for k in groups["ofm"][oi, fi, meeting]), 0) == model.y[oi, fi]
            )
