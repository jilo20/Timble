import pyomo.environ as pyo

from .constraints.assignment import add_assignment
from .constraints.block import add_block
from .constraints.duration import add_duration
from .constraints.faculty import add_faculty
from .constraints.room import add_room
from .objective import add_objective
from .variables import add_variables


def build_model(scenario):
    model = pyo.ConcreteModel("Timble room-waste minimization")
    groups = add_variables(model, scenario)
    for add in [add_assignment, add_faculty, add_room, add_block, add_duration]:
        add(model, scenario, groups)
    add_objective(model, scenario)
    return model
