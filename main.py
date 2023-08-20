import pandas as pd

from pyomo.opt import SolverFactory
from pyomo.environ import *


# Path
path_in = '01_Input/'
path_out = '02_Output/'

# Select Solver
opt = SolverFactory('cbc')
#opt.options['MIPGap'] = 0.05
#opt.options['TimeLimit'] = 3600

# Create DataPortal
data = DataPortal()

# Read Time Series
data.load(filename=path_in+'Gas_Price.csv',
          index='t',
          param='Gas_Price')
data.load(filename=path_in+'Power_Price.csv',
          index='t',
          param='Power_Price')
data.load(filename=path_in+'Capacity_Price.csv',
          index='t',
          param='Capacity_Price')
data.load(filename=path_in+'BHKWCapacityAllowance.csv',
          index='t',
          param='BHKWCapacityAllowance')

# Read BHKW Performance Data
df_BHKW = pd.read_csv(path_in+'BHKW.csv', index_col=0)

# Define abstracte model
m = AbstractModel()

# Define sets
m.t = Set(ordered=True)

# Define parameters
m.Gas_Price = Param(m.t)
m.Power_Price = Param(m.t)
m.Capacity_Price = Param(m.t)
m.BHKWCapacityAllowance = Param(m.t)

# Define Binary Variables
m.BHKW_Bin = Var(m.t,
                 within=Binary,
                 doc='Online')

# Define Continuous Variables
m.BHKW_Gas = Var(m.t,
                 domain=NonNegativeReals,
                 doc='Fuel Consumption')
m.BHKW_Power = Var(m.t,
                   domain=NonNegativeReals,
                   doc='Power Production')
m.BHKW_Heat = Var(m.t,
                  domain=NonNegativeReals,
                  doc='Heat Production')

# Additional Variables For The Capacity Price
m.BHKW_Helper = Var(m.t,
                    domain=NonNegativeReals,
                    doc='Helper')
m.BHKW_PayCapacityPrice = Var(m.t,
                              domain=NonNegativeReals,
                              doc='Pay The Capacity Price')
m.BHKW_AdditionalCapacityAllowance = Var(m.t,
                                         domain=NonNegativeReals,
                                         doc='Additional Capacity Allowance')
m.BHKW_CapacityAllowance = Var(m.t,
                               domain=NonNegativeReals,
                               doc='Capacity Allowance')

# BHKW Constraints
def PowerMax(m, t):
    """ Power Max Constraint """
    return m.BHKW_Power[t] <= df_BHKW.loc['Max', 'Power']*m.BHKW_Bin[t]

m.PowerMax_Constraint = Constraint(m.t, rule=PowerMax)


def PowerMin(m, t):
    """ Power Min Constraint """
    return df_BHKW.loc['Min', 'Power']*m.BHKW_Bin[t] <= m.BHKW_Power[t]

m.PowerMin_Constraint = Constraint(m.t, rule=PowerMin)


def GasDependsOnPower(m, t):
    """ Gas = a*Power+b*Bin Constraint """
    value_GasMax = df_BHKW.loc['Max', 'Gas']
    value_GasMin = df_BHKW.loc['Min', 'Gas']
    value_PowerMax = df_BHKW.loc['Max', 'Power']
    value_PowerMin = df_BHKW.loc['Min', 'Power']

    a = (value_GasMax-value_GasMin)/(value_PowerMax-value_PowerMin)
    b = value_GasMax-a*value_PowerMax

    return m.BHKW_Gas[t] == a*m.BHKW_Power[t]+b*m.BHKW_Bin[t]

m.GasDependsOnPower_Constraint = Constraint(m.t, rule=GasDependsOnPower)


def HeatDependsOnPower(m, t):
    """ Heat = a*Power+b*Bin Constraint """
    value_HeatMax = df_BHKW.loc['Max', 'Heat']
    value_HeatMin = df_BHKW.loc['Min', 'Heat']
    value_PowerMax = df_BHKW.loc['Max', 'Power']
    value_PowerMin = df_BHKW.loc['Min', 'Power']

    a = (value_HeatMax-value_HeatMin)/(value_PowerMax-value_PowerMin)
    b = value_HeatMax-a*value_PowerMax

    return m.BHKW_Heat[t] == a*m.BHKW_Power[t]+b*m.BHKW_Bin[t]

m.HeatDependsOnPower_Constraint = Constraint(m.t, rule=HeatDependsOnPower)

# Capacity Price Constraints
def BHKWHelperMax_Expression(m, t):
    return m.BHKW_Helper[t] <= df_BHKW.loc['Max', 'Gas']

m.BHKWHelperMax_Constraint = Constraint(m.t, rule=BHKWHelperMax_Expression)


def BHKWPayCapacityPriceMax_Expression(m, t):
    return m.BHKW_PayCapacityPrice[t] <= df_BHKW.loc['Max', 'Gas']

m.BHKWPayCapacityPriceMax_Constraint = Constraint(m.t, rule=BHKWPayCapacityPriceMax_Expression)


def BHKWAdditionalCapacityAllowanceMax_Expression(m, t):
    if t == m.t.last():
        return m.BHKW_AdditionalCapacityAllowance[t] <= 0
    else:    
        return m.BHKW_AdditionalCapacityAllowance[t] <= df_BHKW.loc['Max', 'Gas']

m.BHKWAdditionalCapacityAllowanceMax_Constraint = Constraint(m.t, rule=BHKWAdditionalCapacityAllowanceMax_Expression)


def BHKWCapacityAllowanceMax_Expression(m, t):
    return m.BHKW_CapacityAllowance[t] <= m.BHKWCapacityAllowance[t]

m.BHKWCapacityAllowanceMax_Constraint = Constraint(m.t, rule=BHKWCapacityAllowanceMax_Expression)


def BHKWAdditionalCapacityAllowance_Expression(m, t):
        if t == m.t.first():
            return m.BHKW_AdditionalCapacityAllowance[t] == 0
        else:
            return (m.BHKW_AdditionalCapacityAllowance[t] ==
                    m.BHKW_AdditionalCapacityAllowance[t-1] +
                    m.BHKW_Helper[t-1] -
                    m.BHKW_PayCapacityPrice[t])

m.BHKWAdditionalCapacityAllowance_Constraint = Constraint(m.t, rule=BHKWAdditionalCapacityAllowance_Expression)


def BHKWCapacityLink_Expression(m, t):
    return 0 <= -m.BHKW_Gas[t]+m.BHKW_Helper[t]+m.BHKW_AdditionalCapacityAllowance[t]+m.BHKW_CapacityAllowance[t]

m.BHKWCapacityLink_Constraint = Constraint(m.t, rule=BHKWCapacityLink_Expression)


# Objective Function
def obj_expression(m):
    """ Objective Function """
    return (sum(m.BHKW_Gas[t]*m.Gas_Price[t] for t in m.t)+
            sum(m.BHKW_PayCapacityPrice[t]*m.Capacity_Price[t] for t in m.t)-
            sum(m.BHKW_Power[t]*m.Power_Price[t] for t in m.t))

m.obj = Objective(rule=obj_expression, sense=minimize)

# Create instanz
instance = m.create_instance(data)

# Solve the optimization problem
results = opt.solve(instance,
                    logfile=path_out+'Logfile_Output.log',
                    symbolic_solver_labels=True,
                    tee=True,
                    load_solutions=True)

# Write Results
results.write()

""" Write Output Time Series """
df_output = pd.DataFrame()
df_parameters = pd.DataFrame()
df_variables = pd.DataFrame()

for t in instance.t.data():
    # Write Parameter
    for parameter in instance.component_objects(Param, active=True):
        name = parameter.name
        df_parameters[name] = [value(parameter[t]) for t in instance.t]
    # Write Variables
    for variable in m.component_objects(Var, active=True):
        name = variable.name
        df_variables.loc[t, name] = instance.__getattribute__(name)[t].value
df_output = pd.concat([df_parameters, df_variables], axis=1)

df_output.to_csv(path_out+'Timeseries_Output.csv')
