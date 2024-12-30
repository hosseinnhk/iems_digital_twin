from source.energy_storage import energy_storage as es

ess = es.EnergyStorageModel()

ess.end_of_life = 11

print(ess.__repr__())


