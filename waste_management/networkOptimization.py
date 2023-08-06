from pyomo.environ import ConcreteModel, Var, Objective, NonNegativeReals, Constraint, NonNegativeIntegers
from pyomo.environ import *
import pandas as pd
import time

s = time.time()
M = ConcreteModel()
year = '2018'
sites = 2417

forecast_demand = pd.read_csv('waste_management/forecast_arima_2018-19.csv')
print(forecast_demand.columns)


def demand_function(M, i, ):
    return forecast_demand[year].iloc[i]

distance_df = pd.read_csv('waste_management/dataset/Distance_Matrix.csv')

distance_np = distance_df.values
def distance_function(M, i, j):
    return distance_np[i][j]
forecast_demand_dict = forecast_demand.set_index('Index').to_dict()


M.I = RangeSet(sites)
M.J = RangeSet(sites)
M.K = RangeSet(sites)
M.d = Param(M.I, initialize=demand_function)
M.distance = Param(M.I, M.J, initialize=distance_function)

CAP_Depot = 20000
CAP_Refinery = 100000

M.pallet = Var(M.J, M.K, within=NonNegativeReals)
M.biomass = Var(M.I, M.J, within=NonNegativeReals)
M.x = Var(M.I, within=Binary) #selected as 
M.y = Var(M.I, within=Binary)

r = 1.5
a, b, c = 1, 25, 600


def obj_expression(M):
    return a * quicksum(M.ds[i, j] * M.dist[i, j] for i in M.I for j in M.J) + c * quicksum(
        M.scs[j] + r * M.fcs[j] for j in M.J)


M.OBJ = Objective(rule=obj_expression, sense=minimize)


def c2(M, j):
    return M.biomass[i] <= M.d[i]
M.c2_c = Constraint(M.J, rule=c2)


def c3(M, j):
    return M.scs[j] >= M.scs_e[j]


M.c4_c = Constraint(M.J, rule=c4)


def c42(M, j):
    return M.fcs[j] >= M.fcs_e[j]


M.c42_c = Constraint(M.J, rule=c42)


def c5(M, j):
    return quicksum(M.ds[i, j] for i in M.I) <= M.scs[j] * CAP_scs + M.fcs[j] * CAP_fcs


M.c5_c = Constraint(M.J, rule=c5)


def c6(M, i):
    return quicksum(M.ds[i, j] for j in M.J) == forecast_demand_dict[year][i]


M.c6_c = Constraint(M.J, rule=c6)

print('Modeling done...')
M.write("network_opt.lp")
solvername = 'cplex'
opt = SolverFactory(solvername)
# opt.options["preprocessing_presolve"]='n'
# opt.options["mipgap"]=0.05
results = opt.solve(M, tee=True)
print(results)
result_data = []
for j in M.J:
    result_data.append(
        {"data_type": 'SCS', "demand_point_index": None, "supply_point_index": j, "value": M.scs[j].value, })
for j in M.J:
    result_data.append(
        {"data_type": 'FCS', "demand_point_index": None, "supply_point_index": j, "value": M.fcs[j].value, })
for i in M.I:
    for j in M.J:
        result_data.append(
            {"data_type": 'DS', "demand_point_index": i, "supply_point_index": j, "value": M.ds[i, j].value, })

result_summary = pd.DataFrame(result_data)
result_summary.to_csv('result.csv')
print(time.time() - s)
