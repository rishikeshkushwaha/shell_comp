from pyomo.environ import ConcreteModel, Var, Objective, NonNegativeReals, Constraint, NonNegativeIntegers
from pyomo.environ import *
import pandas as pd
from utils import haversine
import time

s = time.time()
M = ConcreteModel()
year = '2019'
M.I = RangeSet(0, 4095)
M.J = RangeSet(0, 99)

forecast_demand = pd.read_csv('forecasted_demand_2019.csv')
infra = pd.read_csv('exisiting_EV_infrastructure_2018.csv')
forecast_demand[year] = forecast_demand[year] * 1.1


def demand_function(M, i, ):
    return forecast_demand[year].iloc[i]


def scs_function(M, j):
    return infra['existing_num_SCS'].iloc[j]


def fcs_function(M, j):
    return infra['existing_num_FCS'].iloc[j]


def ps_function(M, j):
    return infra['total_parking_slots'].iloc[j]


forecast_demand_dict = forecast_demand.set_index('demand_point_index').to_dict()
infra_dict = infra.set_index('supply_point_index').to_dict()


def dist_func(M, i, j):
    lat1 = forecast_demand_dict['x_coordinate'][i]
    long1 = forecast_demand_dict['y_coordinate'][i]
    lat2 = infra_dict['x_coordinate'][j]
    long2 = infra_dict['y_coordinate'][j]
    return haversine(long1, lat1, long2, lat2)


M.d = Param(M.I, initialize=demand_function)
M.scs_e = Param(M.J, initialize=scs_function)
M.fcs_e = Param(M.J, initialize=fcs_function)
M.ps = Param(M.J, initialize=ps_function)

CAP_scs = 200
CAP_fcs = 400

M.dist = Param(M.I, M.J, initialize=dist_func)
M.ds = Var(M.I, M.J, within=NonNegativeReals)
M.scs = Var(M.J, within=NonNegativeIntegers)
M.fcs = Var(M.J, within=NonNegativeIntegers)

r = 1.5
a, b, c = 1, 25, 600


def obj_expression(M):
    return a * quicksum(M.ds[i, j] * M.dist[i, j] for i in M.I for j in M.J) + c * quicksum(
        M.scs[j] + r * M.fcs[j] for j in M.J)


M.OBJ = Objective(rule=obj_expression, sense=minimize)


def c3(M, j):
    return M.scs[j] + M.fcs[j] >= M.ps[j]


M.c3_c = Constraint(M.J, rule=c3)


def c4(M, j):
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
