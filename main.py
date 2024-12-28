from source.energy_storage import energy_storage as es

ess = es.EnergyStorageModel()



ess._discharge_current_max = 26.6

print(ess.__repr__())

