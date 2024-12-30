from source.energy_storage import energy_storage as es

# ess = es.EnergyStorageModel()

# ess.end_of_life = 11


# print(ess.__repr__())

# import pybamm


# model = pybamm.lithium_ion.DFN()  # Doyle-Fuller-Newman model
# parameter_values = pybamm.ParameterValues("Chen2020")

# parameter_values.update({"Number of cells connected in series to make a battery": 100})
# parameter_values.update({"Number of electrodes connected in parallel to make a cell": 16})

# sim = pybamm.Simulation(model, parameter_values=parameter_values)

# sim.solve([0, 3600])  # solve for 1 hour
# sim.plot() 

ess = es.EnergyStorageModel()

Parameters = {}
Parameters['cell_model'] = 'DFN'
Parameters['cell_chemistry'] = 'Chen2020'

model, params = ess.initialize_pybamm_model(Parameters)

