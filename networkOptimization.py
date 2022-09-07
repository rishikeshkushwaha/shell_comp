from pyomo.environ import ConcreteModel, Var, Objective, NonNegativeReals, Constraint
from pyomo.environ import *

M = ConcreteModel()

M.I = Set(RangeSet(4095))
M.J = Set(RangeSet(99))

M.d = Param(M.I, rule=demand)
M.x = Var([1,2], domain=NonNegativeReals)

M.OBJ = Objective(expr = 2*M.x[1] + 3*M.x[2])

M.Constraint1 = Constraint(expr = 3*M.x[1] + 4*M.x[2] >= 1)