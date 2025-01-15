from source.energy_storage import energy_storage as es
import matplotlib.pyplot as plt
import time
import random


ess = es.EnergyStorageModel()

# ess._attributes["end_of_life_point [%]"] = 11
# ess.state_of_charge = 50

# print(ess.__repr__())
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
for j in range (50):
    for i in range(20):
        if i <10: current = random.uniform(0, 20)
        else: current = -random.uniform(0, 20)
        start_time = time.time()
        _, ess.state = ess.run_model(current= current, time_duration=60, ambient_temp=30.0, previous_state=ess.state)
        end_time = time.time()
        # print(f"Time taken for simulation: {end_time - start_time}")
        # print("-------------------------------------")
        # print(ess.report_state())
        # print("=====================================")
        results.append(ess.report_state())

state_of_charge = [result["state_of_charge"][0] for result in results]
state_of_health = [result["state_of_health"][0] for result in results]
current = [result["current"][0] for result in results]
temperature = [result["temperature"][0] for result in results]
x_steps = list(range(len(results)))



fig, axs = plt.subplots(4, 1, figsize=(6, 12))
fig.suptitle("Battery Parameters Over Time", fontsize=12)

axs[0].plot(x_steps, state_of_charge, label="State of Charge (%)", color="blue")
axs[0].set_title("State of Charge")
axs[0].set_xlabel("Time Steps")
axs[0].set_ylabel("State of Charge (%)")
axs[0].grid()
axs[0].legend()


axs[1].plot(x_steps, state_of_health, label="State of Health (%)", color="green")
axs[1].set_title("State of Health")
axs[1].set_xlabel("Time Steps")
axs[1].set_ylabel("State of Health (%)")
axs[1].grid()
axs[1].legend()


axs[2].plot(x_steps, current, label="Current (A)", color="orange")
axs[2].set_title("Current")
axs[2].set_xlabel("Time Steps")
axs[2].set_ylabel("Current (A)")
axs[2].grid()
axs[2].legend()


axs[3].plot(x_steps, temperature, label="Temperature (°C)", color="red")
axs[3].set_title("Temperature")
axs[3].set_xlabel("Time Steps")
axs[3].set_ylabel("Temperature (°C)")
axs[3].grid()
axs[3].legend()


plt.tight_layout() 
plt.show()



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





