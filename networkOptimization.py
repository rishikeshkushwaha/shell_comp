from pyomo.environ import ConcreteModel, Var, Objective, NonNegativeReals, Constraint
from pyomo.environ import *
import pandas as pd

M = ConcreteModel()
year = 2019
M.I = Set(RangeSet(4095))
M.J = Set(RangeSet(99))


def demand_function(year):
    forecast_demand = pd.read_csv('forecasted_demand_2019.csv')
    return forecast_demand['2019']


M.d = Param(M.I, rule=demand)

M.x = Var([1,2], domain=NonNegativeReals)

M.OBJ = Objective(expr = 2*M.x[1] + 3*M.x[2])

M.Constraint1 = Constraint(expr = 3*M.x[1] + 4*M.x[2] >= 1)