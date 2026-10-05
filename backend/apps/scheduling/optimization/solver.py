import math
import time

from pyomo.contrib.appsi.solvers import Highs

from .model_builder import build_model


def finite(value):
    return float(value) if value is not None and math.isfinite(value) else None


def solve(scenario, time_limit=60):
    started = time.perf_counter()
    model = build_model(scenario)
    solver = Highs()
    solver.config.load_solution = False
    solver.config.time_limit = time_limit
    solver.highs_options = {"threads": 1, "random_seed": 0, "mip_rel_gap": 0.0}
    result = solver.solve(model)
    info = (
        solver._solver_model.getInfo()
    )  # Genuine native HiGHS metrics; covered by integration tests.
    feasible = result.best_feasible_objective is not None
    termination = result.termination_condition.name
    assignments = []
    if feasible:
        solver.load_vars()
        for key in model.C:
            if model.x[key].value is not None and model.x[key].value > 0.5:
                o, m, f, r, d, p = key
                assignments.append(
                    {
                        "offering": o,
                        "meeting": m,
                        "faculty": f,
                        "room": r,
                        "day": d,
                        "start": p,
                        "duration": scenario.offerings[o - 1]["duration"],
                    }
                )
    status = (
        "OPTIMAL"
        if termination == "optimal"
        else (
            "FEASIBLE_LIMIT"
            if feasible
            else ("INFEASIBLE" if termination == "infeasible" else "NO_SOLUTION")
        )
    )
    return {
        "status": status,
        "diagnostic": termination,
        "assignments": assignments,
        "objective_value": finite(result.best_feasible_objective),
        "best_bound": finite(result.best_objective_bound),
        "mip_gap": finite(info.mip_gap) if feasible else None,
        "nodes_explored": int(info.mip_node_count) if info.mip_node_count >= 0 else None,
        "elapsed_seconds": time.perf_counter() - started,
    }
