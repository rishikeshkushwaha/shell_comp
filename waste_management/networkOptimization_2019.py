# from pyomo.environ import ConcreteModel, Var, Objective, NonNegativeReals, Constraint, NonNegativeIntegers
from pyomo.environ import *
import pandas as pd
import time
import os
os.environ['NEOS_EMAIL'] = 'rdsawant25@gmail.com'
neos= False
s = time.time()
M = ConcreteModel()
year = '2019'
sites = 2418
big_M = 19999.99
factor = 1.1
forecast_demand = pd.read_csv("waste_management/forecast_arima_2018-19.csv")

potential_depot_refinery = pd.read_csv("waste_management/df_potential_depot_refinery_4.csv")
depot_loc = (potential_depot_refinery[potential_depot_refinery['Potential_depot']==True]['Index'].values)
ref_loc = (potential_depot_refinery[potential_depot_refinery['Potential_refinery']==True]['Index'].values)

distance_df = pd.read_csv('waste_management/dataset/Distance_Matrix.csv')
result = pd.read_csv('result_2418_3_2018.csv')
print(result.dtypes)
distance_np = distance_df.values
def distance_function(M, i, j):
    return distance_np[i][j]
forecast_demand_dict = forecast_demand.set_index('Index').to_dict()

def demand_function(M, i, ):
    return factor*round(forecast_demand_dict['2018'][i-1],2)

M.I = RangeSet(sites)
M.J = [j+1 for j in depot_loc]
M.K = [k+1 for k in ref_loc]
M.d = Param(M.I, initialize=demand_function)
# M.distance = Param(M.I, M.J, initialize=distance_function)

CAP_Depot = 19999.99
CAP_Refinery = 99999.99
M.pallet = Var(M.J, M.K, within=NonNegativeReals)
M.biomass = Var(M.I, M.J, within=NonNegativeReals)
M.depot = Var(M.I, within=Binary) #selected as
M.refinery = Var(M.I, within=Binary)
M.x = Var(M.J, within=Binary) # demand served or not
a, b, c = 0.001, 1, 1
def distance_cost():
    return quicksum(round(distance_np[i - 1][j - 1], 2) * M.biomass[i, j] for i in M.I for j in M.J) \
        + quicksum(round(distance_np[j - 1][k - 1], 2) * M.pallet[j, k] for j in M.J for k in M.K)
def underutilisation_cost():
    return CAP_Depot-quicksum(M.biomass[i,j] for i in M.I for j in M.J) + c*CAP_Refinery-quicksum(M.pallet[j,k] for j in M.J for k in M.K)

print('data preprocessing done --------------------------------')

obj = 3
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
depots = result[(result['year']==20182019)&(result['data_type']=='depot_location')]['source_index'].values
depots = [i+1 for i in depots if i < sites]
refinery = result[(result['year']==20182019)&(result['data_type']=='refinery_location')]['source_index'].values
refinery = [i+1 for i in refinery if i < sites]
def fixing_depot_refinery():
    M.fix_constraints = ConstraintList()
    for j in M.J:
        if j in depots:
            M.depot[j].fix(1)
        else:
            M.depot[j].fix(0)
    for j in M.K:
        if j in refinery:
            M.refinery[j].fix(1)
        else:
            M.refinery[j].fix(0)

fixing_depot_refinery()
def c2(M, i):
    return quicksum(M.biomass[i, j] for j in M.J)<= M.d[i]
M.c2_c = Constraint(M.I, rule=c2)

def all_demand_served(M):
    return quicksum(M.x[i] for i in M.I) == sites
# M.all_demand_served_c = Constraint(rule=all_demand_served)
def c22(M, i,j):
    return M.biomass[i, j] <= M.d[i]
M.c22_c = Constraint(M.I,M.J, rule=c22)

def c3(M, j):
    return quicksum(M.biomass[i, j] for i in M.I) <= CAP_Depot * M.depot[j]
M.c3_c = Constraint(M.J, rule=c3)
print('c3 done', time.time()-s)


def c4(M, k):
    return quicksum(M.pallet[j, k] for j in M.J) <= CAP_Refinery * M.refinery[k]
M.c4_c = Constraint(M.K, rule=c4)
print('c4 done', time.time()-s)


def c5(M):
    return quicksum(M.depot[j] for j in M.J) <= len(depots)
M.c5_c = Constraint(rule=c5)
print('c5 done', time.time()-s)

def c6(M):
    return quicksum(M.refinery[k] for k in M.K) <= len(refinery)
M.c6_c = Constraint(rule=c6)
print('c6 done', time.time()-s)

def c7(M):
    return quicksum(M.pallet[j, k] for j in M.J for k in M.K) >= 0.8 * quicksum(M.d[i] for i in M.I)
M.c7_c = Constraint(rule=c7)
print('c7 done', time.time()-s)

def flow_balance(M,j):
    return quicksum(M.biomass[i, j] for i in M.I) <= quicksum(M.pallet[j,k] for k in M.K)
# M.flow_balance_c = Constraint(M.J, rule=flow_balance)
print('c flow done', time.time()-s)

def c8(M, j):
    return quicksum(M.biomass[i, j] for i in M.I) == quicksum(M.pallet[j, k] for k in M.K) #<= 0.00001
M.c8_c = Constraint(M.J, rule=c8) # Same as flow balance

def c82(M, j):
    return quicksum(M.pallet[j, k] for k in M.K) - quicksum(M.biomass[i, j] for i in M.I)  <= 0.00001
# M.c82_c = Constraint(M.J, rule=c82) # Same as flow balance
def c9(M,j,k):
    return M.pallet[j, k] <= big_M * M.depot[j]
M.c9_c = Constraint(M.J,M.K, rule=c9)

# M.pprint()
print('Modeling done...',time.time()-s)
# M.write("network_opt_"+str(sites)+".lp")
if neos:
    solver_manager = SolverManagerFactory('neos')
    results = solver_manager.solve(M, opt='cplex')
else:
    solvername = 'gurobi'
    opt = SolverFactory(solvername, tee=True)
    opt.options["Presolve"]=1
    opt.options["MIPGap"]=0.0
    # opt.options["Cuts"]=0.0
    opt.options["Heuristics"]=1
    results = opt.solve(M, tee=True)
print(results)
result_data = []

for j in M.J:
    if value(M.depot[j]) == 1:
        result_data.append(
            {"year": 20182019, "data_type": 'depot_location', "source_index": j-1, "destination_index": None,"value": None})

for k in M.K:
    if value(M.refinery[k]) == 1:
        result_data.append(
            {"year": 20182019, "data_type": 'refinery_location', "source_index": k-1, "destination_index": None,"value": None})

for i in M.I:
    result_data.append({"year": year, "data_type": 'biomass_forecast', "source_index": i-1, "destination_index": None,
         "value": demand_function(M,i)})
# for i in M.I:
#         result_data.append(
#             {"data_type": 'biomass_forecast', "year": 2019, "source_index": i-1, "destination": None,"value": forecast_demand.iloc[i-1]*1.2})

for i in M.I:
    for j in M.J:
        if value(M.biomass[i, j])>0.0000001:
            result_data.append({ "year": year, "data_type": 'biomass_demand_supply', "source_index": i - 1, "destination_index": j - 1,
                 "value": value(M.biomass[i, j])})

for j in M.J:
    for k in M.K:
        if value(M.pallet[j, k])>0.0000001:
            result_data.append({"year": year, "data_type": 'pellet_demand_supply', "source_index": j - 1, "destination_index": k - 1,
                 "value": value(M.pallet[j, k])})
result_summary = pd.DataFrame(result_data)
result_summary.to_csv('result_'+str(sites)+'_'+str(obj)+'_'+str(year)+'.csv',index=False)
print(time.time() - s)

# for v_data in M.component_data_objects(Var, descend_into=True):
#     print("Found: " + v_data.name + ", value = " + str(value(v_data)))