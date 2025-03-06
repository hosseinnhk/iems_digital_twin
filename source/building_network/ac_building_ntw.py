
import pandapower as pp
from pandapower.control import controller
import pandapower.topology as top
import networkx as nx


class BuildingElectricityNetwork:
    def __init__(self, name, grid_voltage=0.23):
        
        self.net = pp.create_empty_network()
        self.grid_voltage = grid_voltage
        
        self.name = name
        
        self.dc_voltage = dc_voltage
        self.pv_output_power = 0.0
        self.ess_exchange_power = 0.0
        self.demand = 0.0
        self.pv_inverter_efficiency = 0.95
        self.ess_inverter_efficiency = 0.95
        self.ac_dc_converter_efficiency = 0.95
        self.dc_ac_converter_efficiency = 0.95
        self.ac_dc_converter_rated_power = 0.0
        self.battery_mode = "discharging"
        self.ess_initial_soc = 0.0
        self.ess_capacity = 0.0

        self._establish_network() 
        self._add_pv_setup()
        self._add_battery_storage()
        self._add_bi_ac_dc_converter()
        
        # self._add_dc_dc_socket()
        # self._add_ev_charger()
        # self.run_simulation()
        

    def _establish_network(self):
        
        self.network = pp.create_empty_network() 
        self.ext_grid_1 = pp.create_ext_grid(self.network, bus=self.grid_bus_1, vm_pu=1.0, max_p_mw= 0.005, min_p_mw=-0.005, name="grid connection 1")
        self.ext_grid_2 = pp.create_ext_grid(self.network, bus=self.grid_bus_2, vm_pu=1.0, max_p_mw= 0.005, min_p_mw=-0.005, name="grid connection 2")
        self.ext_grid_3 = pp.create_ext_grid(self.network, bus=self.grid_bus_3, vm_pu=1.0, max_p_mw= 0.005, min_p_mw=-0.005, name="grid connection 3")
        
        self.grid_bus_1 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="grid connection bus 1")
        self.grid_bus_2 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="grid connection bus 2")
        self.grid_bus_3 = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="grid connection bus 3")
        
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

        self.mg = top.create_nxgraph(self.network)

    def _add_pv_setup(self):
        
        # dc_to_dc_loss = (1 - self.pv_dc_bus_effieciency) * self.pv_output_power  # loss in kW
        
        self.pv_conv_loss = pp.create_load(self.network,  
            bus=self.dc_bus_pv, 
            p_mw= 0.0,
            name="pv converter loss"
        ) 

        # dc_power = self.pv_output_power * self.pv_dc_bus_effieciency  # power injected into pv dc bus
        self.pv_setup = pp.create_sgen(self.network, 
            bus = self.dc_bus_pv, 
            p_mw = 0.0, 
            q_mvar=0.0,
            sn_mva=0.0, # Nominal power of the generator
            name = "pv setup", 
            type = "PV"
        )
        
    def _add_battery_storage(self):
        # dc_to_dc_loss = (1 - self.ess_dc_bus_efficiency) * self.ess_exchange_power  # loss in kW
        
        self.ess_cov_loss = pp.create_load(self.network, 
            bus = self.dc_bus_ess, 
            p_mw = 0.0, 
            name = "ess dc/dc converter loss"
        ) 

        # ess_power = self.ess_exchange_power * self.ess_dc_bus_efficiency  
    
        self.battery_storage = pp.create_storage(self.network,
            bus = self.dc_bus_ess, 
            p_mw = 0.0,  # Power in MW
            max_e_mwh = 0.0, # The maximum energy content of the storage (maximum charge level)
            min_e_mwh = 0.0, # The minimum energy content of the storage (minimum charge level)
            max_p_mw = 0.0,  # The maximum power input/output of the storage
            min_p_mw = 0.0,  # The minimum power input/output of the storage (chargining)
            max_q_mvar = 0.0,  # The maximum reactive power input/output of the storage
            min_q_mvar = 0.0,  # The minimum reactive power input/output of the storage
            soc_percent = 0.0,  # The state of charge (SOC) of the storage
            controllable = True,  # Whether the storage is controllable
            name = "Battery Storage",
            type="storage"
            )
    
    pp.create_voltage_source_converter(
    net,
    bus=bus_ac2,          # Connected to AC Bus 2
    bus_dc=bus_dc,        # Connected to DC Bus
    control_mode="PQ",    # Active/Reactive power control
    p_mw=10,              # Inject 10 MW into AC Bus 2 (inverter mode)
    q_mvar=0,             # No reactive power
    power_efficiency_percent=100,
    name="VSC2"
)
        
    def _add_bi_ac_dc_converter(self):
        
        self.intelink_bus = pp.create_bus(self.network, vn_kv=self.grid_voltage/1000, name="intelink bus")
        
        self.ac_dc_conv_loss = pp.create_load(
            self.network,
            bus=self.intelink_bus,  
            p_mw = 0.0, 
            name = "ac to dc conversion loss"
        )

        self.dc_ac_conv_loss = pp.create_load(
            self.network,
            bus = self.ac_bus_renewable,  
            p_mw = 0.0,  
            name = "dc to ac conversion loss"
        )

        # Model the AC to DC conversion as a static generator when charging (AC to DC)
        self.ac_to_dc_converter = pp.create_sgen(self.network,
            bus = self.dc_bus_main,  
            p_mw = 0.0,  # Power flow from AC to DC
            q_mvar = 0.0,
            sn_mva = 0.0, # Nominal power of the generator
            max_p_mw = 0.0,  # The maximum power input/output of the storage
            min_p_mw = 0.0,  # The minimum power input/output of the storage (chargining)
            max_q_mvar = 0.0,  # The maximum reactive power input/output of the storage
            min_q_mvar = 0.0,  # The minimum reactive power input/output of the storage
            controllable = True,  # Whether the storage is controllable
            name = "ac to dc converter",
            type = "AC"
        )

        # Model the DC to AC conversion as a static generator when discharging (DC to AC)
        self.dc_to_ac_converter = pp.create_sgen(
            self.network,
            bus=self.ac_bus_renewable,  # Connect to the AC bus
            p_mw=(rated_power * dc_to_ac_efficiency / 1000),  # Power flow from DC to AC
            name="DC to AC Converter",
            type="DC"
        )
        
    def add_load(self, device_type, **kwargs):
        
        if device_type == 'ac_load':
            if kwargs['bus'] == 'ac_bus_1':
                pp.create_load(self.network, bus=self.ac_bus_1, p_kw=kwargs['p_kw'], q_kvar=kwargs['q_kvar'], name=kwargs['name'])
            elif kwargs['bus'] == 'ac_bus_2':
                pp.create_load(self.network, bus=self.ac_bus_2, p_kw=kwargs['p_kw'], q_kvar=kwargs['q_kvar'], name=kwargs['name'])
            elif kwargs['bus'] == 'ac_bus_3':
                pp.create_load(self.network, bus=self.ac_bus_3, p_kw=kwargs['p_kw'], q_kvar=kwargs['q_kvar'], name=kwargs['name'])
        elif device_type == 'ev_charger':
            pp.create_load(self.network, bus=self.ev_bus, p_kw=kwargs['p_kw'], q_kvar=kwargs['q_kvar'], name=kwargs['name'])
        elif device_type == 'dc_load':
            pp.create_load(self.network, bus=self.dc_bus_load, p_kw=kwargs['p_kw'], q_kvar=kwargs['q_kvar'], name=kwargs['name'])       

    
    def simulate(self):

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
        dc_load = self.net.load.at[self.dc_bus, "p_mw"]
        
        ac_power = dc_load / self.efficiency
        
        self.net.sgen.at[self.ac_bus, "p_mw"] = ac_power
        
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
