
import pandapower as pp
from pandapower.control import controller


class BuildingElectricityNetwork:
    def __init__(self, name, grid_voltage=400, dc_voltage=350,):
        self.name = name
        self.grid_voltage = grid_voltage
        self.dc_voltage = dc_voltage
        self.pv_output = 0.0
        self.dc_demand  = 0.0
        self.ac_demand = 0.0
        self.pv_dc_bus_effieciency = 0.98
        self.ess_dc_bus_efficiency = 0.98
        self.dc_bus_ac_bus_efficiency = 0.95
        self.network = pp.create_empty_network()  
        self._establish_network() 
        self._add_dc_pv_converter()
        self._add_bi_ac_dc_converter()
        self._add_dc_ess_converter()
        self._add_dc_dc_socket()
        

    def _establish_network(self):
        
        self.grid_bus = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="grid connection bus")
        self.ac_bus_1 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ac bus 1")
        self.ac_bus_2 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ac bus 2")
        self.ac_bus_3 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ac bus 3")
        self.ev_bus_1 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ev bus 1")
        self.ev_bus_2 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ev bus 2")
        self.ev_bus_3 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ev bus 3")
        
        self.dc_bus_main = pp.create_bus(self.network, vn_kv=0.4, name="dc bus")
        self.dc_bus_pv = pp.create_bus(self.network, vn_kv=0.4, name="pv dc bus")
        self.dc_bus_ess = pp.create_bus(self.network, vn_kv=0.4, name="ess dc bus")

        self.ext_grid_1 = pp.create_ext_grid(self.network, bus=self.ac_bus_1, vm_pu=1.0)
        self.ext_grid_2 = pp.create_ext_grid(self.network, bus=self.ac_bus_2, vm_pu=1.0)
        self.ext_grid_3 = pp.create_ext_grid(self.network, bus=self.ac_bus_3, vm_pu=1.0)
        
        self.switch_1 = pp.create_switch(self.network, self.ac_bus_1, self.dc_bus_main, element=0, closed=True, name="Switch 1")
        self.switch_2 = pp.create_switch(self.network, self.ac_bus_2, self.dc_bus_main, element=0, closed=True, name="Switch 2")
        self.switch_3 = pp.create_switch(self.network, self.ac_bus_3, self.dc_bus_main, element=0, closed=True, name="Switch 3")
        
        self.ev_switch_1 = pp.create_switch(self.network, self.ac_bus_1, self.ev_bus_1, element=0, closed=True, name="EV Switch 1")
        self.ev_switch_2 = pp.create_switch(self.network, self.ac_bus_2, self.ev_bus_2, element=0, closed=True, name="EV Switch 2")
        self.ev_switch_3 = pp.create_switch(self.network, self.ac_bus_3, self.ev_bus_3, element=0, closed=True, name="EV Switch 3")


    def _add_dc_pv_converter(self):
        dc_to_dc_loss = (1 - self.pv_dc_bus_effieciency) * self.pv_output  # loss in kW
        
        pp.create_load(self.network, bus=self.dc_bus_pv, p_mw=dc_to_dc_loss, name="mppt to dc/dc lost")  # loss for mppt converter

        dc_power = self.pv_output * self.pv_dc_bus_effieciency  # power injected into pv dc bus
        pp.create_sgen(self.network, bus=self.dc_bus_pv, p_mw=dc_power, name="pv to main dc bus injection", type="DC")
    
    def _add_bi_ac_dc_converter(self):
        dc_to_ac_loss = (1 - self.dc_bus_ac_bus_efficiency) * self.ac_demand   
        pp.create_load(self.network, bus=self.dc_bus_main, p_mw=dc_to_ac_loss, name="ac/dc to main dc bus lost")  # loss for ac/dc converter
        ac_power  = self.ac_demand * self.dc_bus_ac_bus_efficiency  
        
        
        
    def add_components(self, device_type, **kwargs):
        if device_type == 'ac_load':
            pp.create_load(self.network, bus=self.ac_bus, p_kw=kwargs['p_kw'], q_kvar=kwargs['q_kvar'], name=kwargs['name'])
        elif device_type == 'dc_load':
            pp.create_load(self.network, bus=self.dc_bus, p_kw=kwargs['p_kw'], q_kvar=kwargs['q_kvar'], name=kwargs['name'])
        elif device_type == 'pv':
            pp.create_sgen(self.network, bus=self.dc_bus_pv, p_kw=kwargs['p_kw'], vm_pu=kwargs['vm_pu'], name=kwargs['name'])
        elif device_type == 'line':
            pp.create_line(self.network, from_bus=kwargs['from_bus'], to_bus=kwargs['to_bus'], length_km=kwargs['length_km'], 
                           r_ohm_per_km=kwargs['r_ohm_per_km'], x_ohm_per_km=kwargs['x_ohm_per_km'], c_nf_per_km=kwargs['c_nf_per_km'], max_i_ka=kwargs['max_i_ka'], name=kwargs['name'])
        elif device_type == 'ess':
            pp.create_storage(self.network, bus=self.dc_bus_ess, p_kw=kwargs['p_kw'], max_e_mwh=kwargs['max_e_mwh'],name=kwargs['name'])

    
    def simulate(self):
        """Run the power flow simulation."""
        pp.runpp(self.network)
        
    def get_results(self):
        """Get the results of the simulation."""
        return self.network.res_bus



class ConverterController(controller):
    def __init__(self, net, ac_bus, dc_bus, efficiency=0.95, **kwargs):
        super().__init__(net, **kwargs)
        self.ac_bus = ac_bus
        self.dc_bus = dc_bus
        self.efficiency = efficiency

    def control_step(self):
        # Access power at the DC bus
        dc_load = self.net.load.at[self.dc_bus, "p_mw"]
        
        # Calculate required AC power
        ac_power = dc_load / self.efficiency  # Adjust for losses
        
        # Update AC bus generation or supply
        self.net.sgen.at[self.ac_bus, "p_mw"] = ac_power
        
        # Model converter losses (optional)
        loss = ac_power - dc_load
        # print(f"AC Power: {ac_power} MW, Loss: {loss:.4f} MW")
    
    def is_converged(self):
        return True

class bi_converter_controller(controller):
    def __init__(self, net, ac_bus, dc_bus, efficiency_ac_dc=0.95, efficiency_dc_ac=0.95, **kwargs):
        super().__init__(net, **kwargs)
        self.ac_bus = ac_bus
        self.dc_bus = dc_bus
        self.efficiency_ac_dc = efficiency_ac_dc
        self.efficiency_dc_ac = efficiency_dc_ac

    def control_step(self):
        dc_power = self.net.sgen.at[self.dc_bus, "p_mw"]  # Power at DC bus
        ac_power = self.net.ext_grid.at[self.ac_bus, "p_mw"]  # Power at AC bus

        # If DC side is charging (AC to DC), invert power flow (with efficiency)
        if dc_power > 0:
            ac_power_output = dc_power * self.efficiency_ac_dc
            self.net.ext_grid.at[self.ac_bus, "p_mw"] = ac_power_output  # Inject AC power (charging mode)
        # If DC side is discharging (DC to AC), invert power flow (with efficiency)
        elif dc_power < 0:
            dc_power_input = -ac_power * self.efficiency_dc_ac
            self.net.sgen.at[self.dc_bus, "p_mw"] = dc_power_input  # Inject DC power (discharging mode)

# Example usage
converter_controller = ConverterController(net, ac_bus=bus_ac, dc_bus=bus_dc, efficiency=0.95)
# Example of how to use this class
building_network = BuildingElectricityNetwork(name="Office Building")
building_network.add_device(device_type='load', bus=building_network.grid_bus, p_kw=100, q_kvar=30)
building_network.simulate()
results = building_network.get_results()
print(results)