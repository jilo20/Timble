import pyomo.environ as pyo


def add_duration(model, scenario, groups):
    """Candidate starts satisfy 1 <= p <= |P|-duration[o]+1.
    Occupancy groups include every q in [p,p+duration[o]-1].
    sum(m,f,r,p) x[o,m,f,r,d,p] <= 1: repeated meetings on distinct days.
    """
    model.distinct_days = pyo.ConstraintList()
    for keys in groups["day"].values():
        model.distinct_days.add(sum(model.x[k] for k in keys) <= 1)
