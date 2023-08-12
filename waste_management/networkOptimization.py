from pyomo.environ import ConcreteModel, Var, Objective, NonNegativeReals, Constraint, NonNegativeIntegers
from pyomo.environ import *
import pandas as pd
import time
import os
os.environ['NEOS_EMAIL'] = 'abc@gmail.com'
neos= False
s = time.time()
M = ConcreteModel()
year = '2018'
sites = 500

forecast_demand = pd.read_csv('waste_management\\forecast_arima_2018-19.csv')

distance_df = pd.read_csv('waste_management\\dataset\\Distance_Matrix.csv')

distance_np = distance_df.values
def distance_function(M, i, j):
    return distance_np[i][j]
forecast_demand_dict = forecast_demand.set_index('Index').to_dict()


def demand_function(M, i, ):
    return round(forecast_demand_dict[year][i-1],2)

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

def distance_cost():
    return quicksum(round(distance_np[i-1, j-1],2) * (M.biomass[i, j] + M.pallet[i,j]) for i in M.I for j in M.J)
def underutilisation_cost():
    return CAP_Depot-quicksum(M.biomass[i,j] for i in M.I for j in M.J) + c*CAP_Refinery-quicksum(M.pallet[i,j] for i in M.I for j in M.J)

print('data preprocessing done --------------------------------')

obj = 1
if obj==1:
    exp = a*distance_cost()
elif obj==2:
    exp = underutilisation_cost()
else:
    exp = a*distance_cost() + c*underutilisation_cost()

def obj_expression(M):
    return exp


M.OBJ = Objective(rule=obj_expression, sense=minimize)
print('objective done', time.time()-s)

def c2(M, i,j):
    return M.biomass[i, j] <= M.d[i]
M.c2_c = Constraint(M.I,M.J, rule=c2)
print('c2 done', time.time()-s)

def c22(M, i,j):
    return M.biomass[i, j] <= M.d[j]
# M.c22_c = Constraint(M.I,M.J, rule=c22)

def c3(M, j):
    return quicksum(M.biomass[i, j] for i in M.I) <= 20000 * M.x[j]
M.c3_c = Constraint(M.J, rule=c3)
print('c3 done', time.time()-s)


def c4(M, j):
    return quicksum(M.pallet[i, j] for i in M.I) <= 100000 * M.y[j]
M.c4_c = Constraint(M.J, rule=c4)
print('c4 done', time.time()-s)


def c5(M):
    return quicksum(M.x[i] for i in M.I) <= 25
M.c5_c = Constraint(rule=c5)
print('c5 done', time.time()-s)

def c6(M):
    return quicksum(M.y[i] for i in M.I) <= 5
M.c6_c = Constraint(rule=c6)
print('c6 done', time.time()-s)

def c7(M):
    return quicksum(M.biomass[i, j] for i in M.I for j in M.J) >= 0.8 * quicksum(M.d[i] for i in M.I)
M.c7_c = Constraint(rule=c7)
print('c7 done', time.time()-s)

def flow_balance(M,j):
    return quicksum(M.biomass[i, j] for i in M.I) <= quicksum(M.pallet[j,k] for k in M.K)
M.flow_balance_c = Constraint(M.J, rule=flow_balance)
print('c flow done', time.time()-s)

def c8(M):
    return quicksum(M.biomass[i, j] for i in M.I for j in M.J) <= quicksum(M.pallet[i, j] for i in M.I for j in M.J)
# M.c8_c = Constraint(rule=c8)

print('Modeling done...')
# M.write("network_opt_"+str(sites)+".lp")
if neos:
    solver_manager = SolverManagerFactory('neos')
    results = solver_manager.solve(M, opt='cplex')
else:
    solvername = 'gurobi'
    opt = SolverFactory(solvername, tee=True)
# opt.options["preprocessing_presolve"]='n'
# opt.options["mipgap"]=0.05
    results = opt.solve(M, tee=True)
print(results)
result_data = []
for i in M.I:
    result_data.append(
        {"data_type": 'depot_location', "year": 20182019, "source_index": i, "destination": None,"value": M.x[i].value})
for j in M.J:
    result_data.append(
        {"data_type": 'refinery_location', "year": 20182019, "source_index": j, "destination": None,"value": M.y[j].value})
for i in M.I:
        result_data.append(
            {"data_type": 'biomass_forecast', "year": 2018, "source_index": i-1, "destination": None,"value": forecast_demand.iloc[i-1]})
for i in M.I:
        result_data.append(
            {"data_type": 'biomass_forecast', "year": 2019, "source_index": i-1, "destination": None,"value": forecast_demand.iloc[i-1]*1.2})
for i in M.I:
    for j in M.J:
        result_data.append(
            {"data_type": 'biomass_demand_supply', "year": 2018, "source_index": i - 1, "destination": j-1,
             "value": M.biomass[i,j].value})
for i in M.I:
    for j in M.J:
        result_data.append(
            {"data_type": 'pellet_demand_supply', "year": 2018,"source_index": i - 1, "destination": j-1,
             "value": M.pallet[i,j].value})
result_summary = pd.DataFrame(result_data)
result_summary.to_csv('result_'+str(sites)+'.csv',index=False)
print(time.time() - s)
