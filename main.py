# from source.energy_storage import energy_storage as es

# ess = es.EnergyStorageModel()

# ess.end_of_life = 11


# print(ess.__repr__())

import pybamm

model = pybamm.lithium_ion.DFN()  # Doyle-Fuller-Newman model
sim = pybamm.Simulation(model)
sim.solve([0, 3600])  # solve for 1 hour
sim.plot() 


