from source.energy_storage import energy_storage as es
import matplotlib.pyplot as plt
import time
import random


ess = es.EnergyStorageModel()

parameters = {
    "cell_model": "DFN",
    "cell_chemistry": "Chen2020",
    "time_resolution [s]": 1,
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

# print(ess.report_state())

results = []

for j in range (10):
    current = random.uniform(-20, 20)
    start_time = time.time()
    error_handler, ess.state = ess.run_model(current= current, time_duration=60, ambient_temp=30.0, previous_state=ess.state)
    if error_handler: ess.initialize_pybamm_model(parameters=parameters)
    end_time = time.time()
    
    # print(f"Time taken for simulation: {end_time - start_time}")
    # print("-------------------------------------")
    # print(ess.report_state())
    # print("=====================================")
    results.append(ess.report_state())

# ess.dynamic_plot(ess.state)
plot_parameters = ["state_of_charge", "state_of_health", "current", "temperature"]
ess.plot_results(results, plot_parameters, save_plot=True)



# # plt.plot(results['time'], results['voltage'])
# # discharge_capacities = [
# #     cycle["Discharge capacity [A.h]"].entries for cycle in solution.cycles[-1:]
# # ]

# # discharge_capacities_flat = np.concatenate(discharge_capacities)

# # plt.plot(discharge_capacities_flat)
# # plt.xlabel("Time or Step Index")  # Adjust the label as per your data
# # plt.ylabel("Discharge Capacity [A.h]")
# # plt.title("Discharge Capacity for the Last Three Cycles")
# # plt.show()
# # sorted(sol.summary_variables.all_variables)a
# # ess = es.EnergyStorageModel()





