# Capacity Price Problem

# Introduction
We consider a gas-fired CHP with the name BHKW in a simplified representation of a unit commitment problem.

The CHP is optimized against the electricity market (Power-Price). The cost function, consisting of gas costs (Gas-Price) and electricity revenues, is minimized.

In addition, a capacity price for the purchase of gas from the gas grid is to be modeled as a grd fee.

This approach can also be used to consider specific investment costs in unit commitment problems. This approach can help determine an appropriate performance design for a new asset in a portfolio. 

## Input Data
The performance data of the BHKW is given by
Loadcase | Gas | Power | Heat|
--- |---|---|---|
Min | 2.5 | 1| 1|
Max | 4.8 | 2| 2|

The unity of the values is MW.

Furthermore, the power and gas price in Euro/MWh for one day are given in hourly resolution.
In the further course it is assumed that the produced heat can be consumed or stored. 

In order to adequately reflect the capacity price for gas purchases, there are two additional input time series. The actual capacity price and the already compensated capacity (BHKWCapacityAllowance). 

The already settled power is then taken into account if, for example, the unit commitment problem is used in the context of an operational day-ahead scheduling or the optimization horizon has to be divided into subproblems to reduce complexity.

## Model
The model is structured and commented.

The BHKW is described by 4 variables (Gas, Bin, Power, Heat) and 4 equations. The first two equations constrain the power output depending on the binary varibale, which indicates whether the BHKW is online or offline. The other two equations specify the gas demand and the heat production, respectively, as a linear function of the power production. 

The next block describes the actual capacity price problem. For this purpose 4 additional variables are introduced

Name | Description|
--- |---|
BHKW_Helper | Registers new required capacity |
BHKW_PayCapacityPrice | The capacity (in Euro/MW) still to be paid during optimization |
BHKW_AdditionalCapacityAllowance|Additional power required|
BHKW_CapacityAllowance|Already compensated capacity|

The modeling idea is that the first 3 variables represent a storage for the capacity, which has to be loaded via the variable BHKW_Helper and unloaded at the end of the optimization via the variable BHKW_PayCapacityPrice. The variable BHKW_AdditionalCapacityAllowance then represents the content of this storage.

The focus is then on the equation:

BHKW_Gas $<=$ BHKW_Helper+BHKW_AdditionalCapacityAllowance+BHKW_CapacityAllowance

## Scenarios
In order to understand the modeling idea, we recommend to consider the following scenarios.
Name | Description|
--- |---|
Capacity Price is 0 Eruo/MWh | Base case. The objective function value is -115.2 Euro|
Capacity Price is 23 Euro/MWh | The BHKW is online and the objective function value is -4.8 Eruo. |
Capacity Price is 24 Euro/MWh|The BHKW is offline.|

The already compensated capacity is equal to zero in all szenarios.

For a simple exploratory data analysis you can use the jupyter notebook named Analyse.