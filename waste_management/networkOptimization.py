from pyomo.environ import ConcreteModel, Var, Objective, NonNegativeReals, Constraint, NonNegativeIntegers
from pyomo.environ import *
import pandas as pd
import time
import os
os.environ['NEOS_EMAIL'] = 'rishikeshkushwaha@gmail.com'
neos= True
s = time.time()
M = ConcreteModel()
year = '2018'
sites = 100

forecast_demand = pd.read_csv('waste_management\\forecast_arima_2018-19.csv')
print(forecast_demand.columns)


def demand_function(M, i, ):
    return forecast_demand[year].iloc[i-1]

distance_df = pd.read_csv('waste_management\\dataset\\Distance_Matrix.csv')

distance_np = distance_df.values
def distance_function(M, i, j):
    return distance_np[i][j]
forecast_demand_dict = forecast_demand.set_index('Index').to_dict()


M.I = RangeSet(sites)
M.J = RangeSet(sites)
M.K = RangeSet(sites)
M.d = Param(M.I, initialize=demand_function)
# M.distance = Param(M.I, M.J, initialize=distance_function)

CAP_Depot = 20000
CAP_Refinery = 100000

M.pallet = Var(M.J, M.K, within=PositiveReals)
M.biomass = Var(M.I, M.J, within=PositiveReals)
M.x = Var(M.I, within=Binary) #selected as
M.y = Var(M.I, within=Binary)

a, b, c = 0.001, 1, 1

print('data preprocessing done --------------------------------')
def obj_expression(M):
    return a * quicksum(distance_np[i-1, j-1] * (M.biomass[i, j] + M.pallet[i,j]) for i in M.I for j in M.J)
+ c*CAP_Depot-quicksum(M.biomass[i,j] for i in M.I for j in M.J) + c*CAP_Refinery-quicksum(M.pallet[i,j] for i in M.I for j in M.J)


M.OBJ = Objective(rule=obj_expression, sense=maximize)


def c2(M, i,j):
    return M.biomass[i, j] <= M.d[i]
M.c2_c = Constraint(M.I,M.J, rule=c2)

def c22(M, i,j):
    return M.biomass[i, j] <= M.d[j]
# M.c22_c = Constraint(M.I,M.J, rule=c22)

def c3(M, i):
    return quicksum(M.biomass[i, j] for j in M.J) <= 20000 * M.x[i]
M.c3_c = Constraint(M.I, rule=c3)


def c4(M, i):
    return quicksum(M.pallet[i, j] for j in M.J) <= 100000 * M.y[i]
M.c4_c = Constraint(M.I, rule=c4)


def c5(M):
    return quicksum(M.x[i] for i in M.I) <= 25
# M.c5_c = Constraint(rule=c5)

def c6(M):
    return quicksum(M.y[i] for i in M.I) <= 5


# M.c6_c = Constraint(rule=c6)
def c7(M):
    return quicksum(M.biomass[i, j] for i in M.I for j in M.J) >= 0.8 * quicksum(M.d[i] for i in M.I)


M.c7_c = Constraint(rule=c7)

def c8(M):
    return quicksum(M.biomass[i, j] for i in M.I for j in M.J) <= quicksum(M.pallet[i, j] for i in M.I for j in M.J)


M.c8_c = Constraint(rule=c8)
M.pprint()
print('Modeling done...')
M.write("network_opt_"+str(sites)+".lp", io_options = {"symbolic_solver_labels":True})
if neos == True:
    solver_manager = SolverManagerFactory('neos')
    results = solver_manager.solve(M, opt='cplex')
else:
    solvername = 'cplex'
    opt = SolverFactory(solvername)
# opt.options["preprocessing_presolve"]='n'
# opt.options["mipgap"]=0.05
    results = opt.solve(M, tee=True)
print(results)
result_data = []
# for j in M.J:
#     result_data.append(
#         {"data_type": 'SCS', "demand_point_index": None, "supply_point_index": j, "value": M.scs[j].value, })
# for j in M.J:
#     result_data.append(
#         {"data_type": 'FCS', "demand_point_index": None, "supply_point_index": j, "value": M.fcs[j].value, })
# for i in M.I:
#     for j in M.J:
#         result_data.append(
#             {"data_type": 'DS', "demand_point_index": i, "supply_point_index": j, "value": M.ds[i, j].value, })

result_summary = pd.DataFrame(result_data)
result_summary.to_csv('result.csv')
print(time.time() - s)
