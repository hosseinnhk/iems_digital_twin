from source.energy_storage import energy_storage as es

ess = es.EnergyStorageModel()

# ess._attributes["end_of_life_point [%]"] = 11
# ess.state_of_charge = 50

# print(ess.__repr__())
parameters = {
    "cell_model": "DFN",
    "cell_chemistry": "Chen2020",
    "time_resolution [s]": 3600,
    "nominal_voltage [v]": 345.0,
    "nominal_capacity [Ah]": 25.0,
    "ambient_temperature [°C]": 25.0,
    "current [A]": 0.0,
    "power_max [w]": 5000.0,
    "state_of_health_init [%]": 100.0,
    "state_of_charge_init [%]": 50.0,
    "nominal_cell_voltage [V]": 3.63,
    "discharge_current_max [A]": 20.0,
    "charge_current_max [A]": 10.0,
    "state_of_charge_min [%]": 15.0,
    "state_of_charge_max [%]": 90.0,
    "end_of_life_point [%]": 80.0,
    "charge_efficiency [%]": 96.0,
    "discharge_efficiency [%]": 96.0,
    "temperature_max [°C]": 60.0,
    "c_rate_charge_max": 1.0,
    "c_rate_discharge_max": 1.0,
    }
ess.initialize_pybamm_model(parameters=parameters)

# model = pybamm.lithium_ion.DFN(
#     {
#         "SEI": "solvent-diffusion limited",
#         "SEI porosity change": "true",
#         "lithium plating": "partially reversible",
#         "lithium plating porosity change": "true",  # alias for "SEI porosity change"
#         "particle mechanics": ("swelling and cracking", "swelling only"),
#         "SEI on cracks": "true",
#         "loss of active material": "stress-driven",
#         "calculate discharge energy": "true",  # for compatibility with older PyBaMM versions
#     }
# )


# parameter_values = pybamm.ParameterValues("OKane2022")
# var_pts = {
#     "x_n": 5,  # negative electrode
#     "x_s": 5,  # separator
#     "x_p": 5,  # positive electrode
#     "r_n": 30,  # negative particle
#     "r_p": 30,  # positive particle
# }
# # print(model.variables.search("Capacity"))
# # parameter_values.update({"Number of cells connected in series to make a battery": 1})
# # parameter_values.update({"Number of electrodes connected in parallel to make a cell": 1})

# probe_experiment = pybamm.Experiment(
#     [
#         (
#             "Charge at 1 A until 4.2V",
#             "Hold at 4.2V until 0.01C",
#             "Rest for 4 hours",
#             "Discharge at 0.5A until 2.5V",
#         )
#     ]*10
# ) 

# sim = pybamm.Simulation(model, parameter_values=parameter_values, experiment=probe_experiment , var_pts=var_pts)
# solution = sim.solve(initial_soc=.5)  # solve for 1 hour

# # sim.plot() 
# # sol.plot(["Current [A]", "Voltage [V]"])
# results = {
#     "time": solution["Time [s]"].entries,
#     "voltage": solution["Terminal voltage [V]"].entries,
#     "current": solution["Current [A]"].entries,
#     "power": solution["Power [W]"].entries,
#     'c-rate': solution["C-rate"].entries,
#     'discharge_capacity': solution["Discharge capacity [A.h]"].entries,
#     'discharge_energy': solution["Discharge energy [W.h]"].entries,
#     'battery_voltage': solution["Battery voltage [V]"].entries[-1],
#     'cell_voltage': solution['Voltage [V]'].entries,
#     # "state_of_power": solution["State of power"].entries,
#     # "stored_energy": solution["Stored energy [Wh]"].entries,
#     "x_averaged_temperature": solution["X-averaged cell temperature [C]"].entries,
#     "cell_temperature": solution["Cell temperature [C]"].entries,
#     "total_heating": solution["Total heating [W.m-3]"].entries,
#     # "remained_capacity": solution["Remaining capacity [A.h]"].entries,
#     # "state_of_charge": solution["State of Charge [%]"].entries,
#     # "state_of_health": solution["State of Health [%]"].entries,
#     # "number_of_cycles": solution["Number of cycles"].entries
#     }
# import numpy as np
# import matplotlib.pyplot as plt


# # print(np.size(solution["Total lithium capacity [A.h]"].entries), solution["Discharge capacity [A.h]"].entries)


# # plt.plot(results['time'], results['voltage'])
# # discharge_capacities = [
# #     cycle["Discharge capacity [A.h]"].entries for cycle in solution.cycles[-1:]
# # ]

# # # Optionally, flatten the data if needed and plot

# # discharge_capacities_flat = np.concatenate(discharge_capacities)

# # plt.plot(discharge_capacities_flat)
# # plt.xlabel("Time or Step Index")  # Adjust the label as per your data
# # plt.ylabel("Discharge Capacity [A.h]")
# # plt.title("Discharge Capacity for the Last Three Cycles")
# # plt.show()
# # sorted(sol.summary_variables.all_variables)a
# # ess = es.EnergyStorageModel()

# # Parameters = {
# #     "cell_model": "DFN",
# #     "cell_chemistry": "Chen2020",
# #     "time_resolution [s]": 3600,  
# #     "nominal_voltage [v]": 340.0,
# #     "nominal_cell_voltage [V]": 3.63, 
# #     "nominal_capacity [Ah]": 25.0, 
# #     "power_max [w]": 5000.0,  
# #     "discharge_current_max [A]": 20.0,  
# #     "charge_current_max [A]": 10.0,  
# #     "state_of_health_init [%]": 100.0,  
# #     "state_of_charge_init [%]": 50.0,  
# #     "state_of_charge_min [%]": 15.0,  
# #     "state_of_charge_max [%]": 90.0,  
# #     "charge_efficiency [%]": 96.0,  
# #     "discharge_efficiency [%]": 96.0, 
# #     "ambient_temperature [°C]": 25.0,
# #     "current [A]" : 0.0,
# #     "end_of_life_point [%]" : 80.0,
# #     "temperature_max [°C]" : 60.0,
# #     "c_rate_charge_max": 1.0,
# #     "c_rate_discharge_max": 1.0,
# # }

# # model, params = ess.initialize_pybamm_model(Parameters)
# # print(ess.__repr__())


# import matplotlib.pyplot as plt

# # Function to calculate degradation by extracting the first discharge capacity from the last step of each cycle
# def calculate_degradation(solution):
#     """
#     Extract the first discharge capacity value from the last step of each cycle
#     and plot degradation over cycles.

#     Parameters:
#     solution: PyBaMM solution object with cycle data.
#     start_cycle (int): The cycle number to start the analysis from (default is 1).

#     Returns:
#     List of first discharge capacity values for plotting.
#     """
#     discharge_capacities = []

#     # Iterate through the cycles starting from start_cycle
#     for cycle in solution.cycles:
#         # Take the last step in the current cycle
#         step = cycle.steps[-1]
#         discharge_capacities.append(np.max(step["Discharge capacity [A.h]"].entries))

#     return discharge_capacities

# # Example usage
# if __name__ == "__main__":
#     # Assume `solution` is your PyBaMM solution object with cycle data
#     degradation_values = calculate_degradation(solution)

#     # Plot the degradation over cycles
#     plt.plot(range(1, len(degradation_values) + 1), degradation_values, marker="o")
#     plt.xlabel("Cycle Number")
#     plt.ylabel("First Discharge Capacity [A.h]")
#     plt.title("Capacity Degradation Over Cycles")
#     plt.grid()
#     plt.show()


