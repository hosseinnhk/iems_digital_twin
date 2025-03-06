import pandapower as pp
import pandapower.timeseries as ts
from pandapower.control import controller
import pandas as pd

class CustomStorageController(controller):
    def __init__(self, net, storage_index, pv_index, load_index, soc_initial=0.5, soc_min=0.2, soc_max=1.0, name=None, **kwargs):
        super().__init__(net, **kwargs)
        self.storage_index = storage_index
        self.pv_index = pv_index
        self.load_index = load_index
        self.soc = soc_initial
        self.soc_min = soc_min
        self.soc_max = soc_max

    def control_step(self):
        pv_output = self.net.sgen.at[self.pv_index, 'p_mw']  
        load_demand = self.net.load.at[self.load_index, 'p_mw']  
        storage = self.net.storage.loc[self.storage_index]

        net_power = pv_output - load_demand  # Positive: excess, Negative: deficit

        if net_power > 0:  # Surplus PV
            charge_power = min(net_power, storage.max_p_mw)  # Max charging limit
            self.soc += charge_power / storage.max_e_mwh  # Update SOC
            self.soc = min(self.soc, self.soc_max)
            self.net.storage.at[self.storage_index, 'p_mw'] = -charge_power  # Negative means charging
        elif net_power < 0 and self.soc > self.soc_min:  # Deficit, and battery has charge
            discharge_power = min(-net_power, storage.max_p_mw)  # Max discharging limit
            self.soc -= discharge_power / storage.max_e_mwh  # Update SOC
            self.soc = max(self.soc, self.soc_min)
            self.net.storage.at[self.storage_index, 'p_mw'] = discharge_power  # Positive means discharging
        else:  # Idle
            self.net.storage.at[self.storage_index, 'p_mw'] = 0

        print(f"Step {self.time_step}: SOC = {self.soc:.2f}")

    def is_converged(self):
        return True

net = pp.create_empty_network()

# Add buses
bus_grid = pp.create_bus(net, vn_kv=0.4, name="Grid")
bus_building = pp.create_bus(net, vn_kv=0.4, name="Building")

# Add components
pp.create_ext_grid(net, bus=bus_grid, vm_pu=1.0)
pp.create_line_from_parameters(net, bus_grid, bus_building, length_km=0.1, r_ohm_per_km=0.1, x_ohm_per_km=0.1, c_nf_per_km=0, max_i_ka=0.1)
load_index = pp.create_load(net, bus=bus_building, p_mw=0.0, name="Load")
pv_index = pp.create_sgen(net, bus=bus_building, p_mw=0.0, name="PV")
storage_index = pp.create_storage(net, bus=bus_building, p_mw=0.0, max_e_mwh=10, max_p_mw=2, name="Battery")

# Create load and PV profiles (replace with real data)
load_data = pd.DataFrame({"load_kw": [5, 6, 7, 8]})  # kW
pv_data = pd.DataFrame({"pv_kw": [0, 3, 5, 2]})  # kW
ds = ts.DataSource(data={'load': load_data['load_kw'] / 1000, 'pv': pv_data['pv_kw'] / 1000})

# Add controllers
ts.control.ConstControl(net, element='load', element_index=load_index, variable='p_mw', data_source=ds, profile_name='load')
ts.control.ConstControl(net, element='sgen', element_index=pv_index, variable='p_mw', data_source=ds, profile_name='pv')
storage_controller = CustomStorageController(net, storage_index=storage_index, pv_index=pv_index, load_index=load_index)

# Run time-series simulation
time_steps = len(load_data)
ts.run_timeseries(net, time_steps=time_steps)




