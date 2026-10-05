import pyomo.environ as pyo


def add_faculty(model, scenario, groups):
    """Occupancy sum <= 1 per (f,d,p); weekly periods <= maximum load.
    For each MUST_TEACH (f,s), sum of y[o,f] over offerings of s >= 1.
    CANNOT and missing-rule pairs have no decision variable.
    """
    model.faculty_collision = pyo.ConstraintList()
    model.must_teach = pyo.ConstraintList()
    model.faculty_load = pyo.ConstraintList()
    for keys in groups["faculty"].values():
        model.faculty_collision.add(sum(model.x[k] for k in keys) <= 1)
    for (fi, si), rule in groups["rules"].items():
        matching = [o for o in scenario.offerings if o["subject"] == si]
        if rule == "MUST_TEACH" and matching:
            model.must_teach.add(sum(model.y[o["index"], fi] for o in matching) >= 1)
    for f in scenario.faculty:
        pairs = [(o, fi) for o, fi in model.E if fi == f["index"]]
        if pairs:
            model.faculty_load.add(
                sum(
                    scenario.offerings[o - 1]["duration"]
                    * scenario.offerings[o - 1]["meetings"]
                    * model.y[o, fi]
                    for o, fi in pairs
                )
                <= f["max_load"]
            )
