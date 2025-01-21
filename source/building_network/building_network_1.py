
import pandapower as pp
from pandapower.control import controller


class BuildingElectricityNetwork:
    def __init__(self, name, grid_voltage=400, dc_voltage=350,):
        self.name = name
        self.grid_voltage = grid_voltage
        self.dc_voltage = dc_voltage
        self.pv_output_power = 0.0
        self.ess_exchange_power = 0.0
        self.dc_demand  = 0.0
        self.ac_demand = 0.0
        self.pv_dc_bus_effieciency = 0.98
        self.ess_dc_bus_efficiency = 0.98
        self.ac_dc_converter_efficiency = 0.95
        self.dc_ac_converter_efficiency = 0.95
        self.ac_dc_converter_rated_power = 0.0
        self.battery_mode = "discharging"
        self.ess_initial_soc = 0.0
        self.ess_capacity = 0.0

        
        self._establish_network() 
        self._add_dc_pv_converter_and_pv()
        self._add_dc_ess_converter_and_storage()
        self._add_bi_ac_dc_converter()
        
        # self._add_dc_dc_socket()
        # self._add_ev_charger()
        # self.run_simulation()
        

    def _establish_network(self):
        
        self.network = pp.create_empty_network() 
        self.ext_grid_1 = pp.create_ext_grid(self.network, bus=self.grid_bus_1, vm_pu=1.0, max_p_mw= 0.005, min_p_mw=-0.005, name="grid connection 1")
        self.ext_grid_2 = pp.create_ext_grid(self.network, bus=self.grid_bus_2, vm_pu=1.0, max_p_mw= 0.005, min_p_mw=-0.005, name="grid connection 2")
        self.ext_grid_3 = pp.create_ext_grid(self.network, bus=self.grid_bus_3, vm_pu=1.0, max_p_mw= 0.005, min_p_mw=-0.005, name="grid connection 3")
        
        self.grid_bus_1 = pp.create_ext_grid(self.network, vn_kv=self.grid_voltage/1000, name="grid connection bus 1")
        self.grid_bus_2 = pp.create_ext_grid(self.network, vn_kv=self.grid_voltage/1000, name="grid connection bus 2")
        self.grid_bus_3 = pp.create_ext_grid(self.network, vn_kv=self.grid_voltage/1000, name="grid connection bus 3")
        
        self.ac_bus_1 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ac bus 1")
        self.ac_bus_2 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ac bus 2")
        self.ac_bus_3 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ac bus 3")
        
        # self.ev_bus_1 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ev bus 1")
        # self.ev_bus_2 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ev bus 2")
        # self.ev_bus_3 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ev bus 3")
        self.ev_bus = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ev bus")
        
        self.ac_bus_renewable = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="ac bus renewable")
        self.dc_bus_load = pp.create_bus(self.network, vn_kv=self.dc_voltage/1000, name="dc bus for dc load")
        self.dc_bus_main = pp.create_bus(self.network, vn_kv=0.4, name="dc bus")
        self.dc_bus_pv = pp.create_bus(self.network, vn_kv=0.4, name="pv dc bus")
        self.dc_bus_ess = pp.create_bus(self.network, vn_kv=0.4, name="ess dc bus")

        self.ac_switch_1 = pp.create_switch(self.network, self.grid_bus_1, element=self.ac_bus_1, et="b", closed=True, name="grid to building ac bus 1 relay")
        self.ac_switch_2 = pp.create_switch(self.network, self.grid_bus_2, element=self.ac_bus_2, et="b", closed=True, name="grid to building ac bus 2 relay")
        self.ac_switch_3 = pp.create_switch(self.network, self.grid_bus_3, element=self.ac_bus_3, et="b", closed=True, name="grid to building ac bus 3 relay")
        
        self.dc_switch_1 = pp.create_switch(self.network, self.ac_bus_1, element=self.ac_bus_renewable, et="b", closed=True, name="renewable bus relay 1")
        self.dc_switch_2 = pp.create_switch(self.network, self.ac_bus_2, element=self.ac_bus_renewable, et="b", closed=True, name="renewable bus relay 2")
        self.dc_switch_3 = pp.create_switch(self.network, self.ac_bus_3, element=self.ac_bus_renewable, et="b", closed=True, name="renewable bus relay 3")
        
        self.ev_switch_1 = pp.create_switch(self.network, self.ac_bus_1, element=self.ev_bus, et="b", closed=False, name="EV charger relay 1")
        self.ev_switch_2 = pp.create_switch(self.network, self.ac_bus_2, element=self.ev_bus, et="b", closed=False, name="EV charger relay 2")
        self.ev_switch_3 = pp.create_switch(self.network, self.ac_bus_3, element=self.ev_bus, et="b", closed=False, name="EV charger relay 3")


    def _add_dc_pv_converter_and_pv(self):
        dc_to_dc_loss=(1-self.pv_dc_bus_effieciency)*self.pv_output_power  # loss in kW
        
        self.pv_conv_loss=pp.create_load(self.network,  
            bus=self.dc_bus_pv, 
            p_mw=(dc_to_dc_loss/1000), 
            name="mppt to dc/dc loss"
        )  # loss for mppt converter

        dc_power = self.pv_output_power * self.pv_dc_bus_effieciency  # power injected into pv dc bus
        self.pv_setup = pp.create_sgen(self.network, 
            bus = self.dc_bus_pv, 
            p_mw = (dc_power/1000), 
            name = "pv to main dc bus injection", 
            type = "DC"
        )
        
    def _add_dc_ess_converter_and_storage(self):
        dc_to_dc_loss = (1 - self.ess_dc_bus_efficiency) * self.ess_exchange_power  # loss in kW
        
        self.ess_cov_loss = pp.create_load(self.network, bus=self.dc_bus_ess, p_mw=(dc_to_dc_loss/1000), name="ess dc/dc converter loss")  # loss for mppt converter

        ess_power = self.ess_exchange_power * self.ess_dc_bus_efficiency  
    
        self.battery_storage = pp.create_storage(
            self.network,
            bus = self.dc_bus_ess, 
            p_mw = ess_power / 1000,  # Power in MW
            max_e_mwh = self.ess_capacity / 1000,  # Energy capacity in MWh
            efficiency = 1, 
            soc_initial = self.ess_initial_soc,  
            name="Battery Storage"
        )
    
    def _add_bi_ac_dc_converter(self):
        dc_to_ac_loss = (1 - self.dc_bus_ac_bus_efficiency) * self.ac_demand   
        pp.create_load(self.network, bus=self.dc_bus_main, p_mw=dc_to_ac_loss, name="ac/dc to main dc bus lost")  # loss for ac/dc converter
        ac_power  = self.ac_demand * self.dc_bus_ac_bus_efficiency  
        
    def _add_bi_ac_dc_converter(self):
        
        ac_to_dc_efficiency = self.ac_dc_converter_efficiency  # Efficiency for AC to DC conversion
        dc_to_ac_efficiency = self.dc_ac_converter_efficiency  # Efficiency for DC to AC conversion

        rated_power = self.ac_dc_converter_rated_power  # Maximum power in kW

        ac_to_dc_loss = (1 - ac_to_dc_efficiency) * rated_power  # Loss in kW

        dc_to_ac_loss = (1 - dc_to_ac_efficiency) * rated_power  # Loss in kW

        self.ac_dc_conv_loss = pp.create_load(
            self.network,
            bus=self.dc_bus_main,  # Connect to the DC bus
            p_mw=(ac_to_dc_loss / 1000),  # Convert kW to MW
            name="AC to DC Conversion Loss"
        )

        self.dc_ac_conv_loss = pp.create_load(
            self.network,
            bus=self.ac_bus_renewable,  # Connect to the AC bus
            p_mw=(dc_to_ac_loss / 1000),  # Convert kW to MW
            name="DC to AC Conversion Loss"
        )

        # Model the AC to DC conversion as a static generator when charging (AC to DC)
        self.ac_to_dc_converter = pp.create_sgen(
            self.network,
            bus=self.dc_bus_main,  # Connect to the DC bus
            p_mw=(rated_power * ac_to_dc_efficiency / 1000),  # Power flow from AC to DC
            name="AC to DC Converter",
            type="AC"
        )

        # Model the DC to AC conversion as a static generator when discharging (DC to AC)
        self.dc_to_ac_converter = pp.create_sgen(
            self.network,
            bus=self.ac_bus_renewable,  # Connect to the AC bus
            p_mw=(rated_power * dc_to_ac_efficiency / 1000),  # Power flow from DC to AC
            name="DC to AC Converter",
            type="DC"
        )

        # Optionally, add logic to switch between charging and discharging mode
        # This could be done using a control system, based on the system’s state
        if self.ac_dc_mode == "charging":
            # Switch to charging mode (AC to DC)
            pp.set_sgen(self.network, self.ac_to_dc_converter, p_mw=(rated_power * ac_to_dc_efficiency / 1000))
            pp.set_sgen(self.network, self.dc_to_ac_converter, p_mw=0)  # No power flow in DC to AC direction
        elif self.ac_dc_mode == "discharging":
            # Switch to discharging mode (DC to AC)
            pp.set_sgen(self.network, self.ac_to_dc_converter, p_mw=0)  # No power flow in AC to DC direction
            pp.set_sgen(self.network, self.dc_to_ac_converter, p_mw=(rated_power * dc_to_ac_efficiency / 1000))        
        
        
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
        if self.battery_mode == "charging":
            pp.set_storage(
                self.network, 
                self.battery_storage, 
                p_mw=self.battery_power * self.battery_dc_bus_efficiency / 1000  # Charging power
            )
        elif self.battery_mode == "discharging":
            pp.set_storage(
                self.network, 
                self.battery_storage, 
                p_mw=-self.battery_power * self.battery_dc_bus_efficiency / 1000  # Discharging power
            )

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