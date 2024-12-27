# import calculations as calc



class EnergyStorageModel:
    
    def __init__(self):
        
        self.cell_voltage = 3.3  # Volts (V)
        self.cell_stored_energy = 3.63  # Watt-hour (Wh)
        self.cell_temperature = 25.0  # Temperature, in Celsius (°C)
        self.cell_capacity = 3.3 # energy storage capacity (Wh)
        
        self.soc = 30.0  # State of Charge, as a percentage
        self.soc_init = 50.0 # Initial State of Charge, as a percentage
        self.soh = 100.0 # State of Health, as a percentage
        self.soh_init = 100.0 # Initial State of Health, as a percentage
        self.voltage = 330.0  # Volts (V)
        self.current = 0.0 # Current, in Amps (A)
        self.temperature = 25.0  # Temperature, in Celsius (°C)``
        self.voltage_max = 340.0  # Voltage, in Volts (V)
        self.c_rate_charge = 1.0 # Charge  c rate
        self.c_rate_discharge = 1.0 # Discharge c rate
        
        self.cell_series_number = 100 # Number of cells in series
        self.parallel_branches = 16 # Number of parallel branches
        
        # constants for the model
        self.discharge_current_max = 30  # Amps (A)
        self.charge_current_max = 4  # Amps (A)
        self.eol = 70  # Percentage (%) - End of Life criteria
        self.soc_min = 15.0 # Minimum State of Charge, as a percentage
        self.soc_max = 90.0 # Maximum State of Charge, as a percentage
        self.cell_nominal_capacity = 1.1  # Ampere-hour (Ah)
        self.internal_resistance = 12.6  # milliohms (mΩ)
        self.battery_charge_efficiency = 0.96  # max 1
        self.battery_discharge_efficiency = 0.96  # max 1
        self.delta_dod = 75  # Percentage (%) - Depth of Discharge variation
        self.cycle_life = 2000  # Cycles for 100% Depth of Discharge (DOD)
        self.calendar_life = 10  # Years
        self.power_max = 5000 # Power, in Watts (W)
        self.current_max = 30.0 # Current, in Amps (A)
        
        self.k_s1 =  -4.092e-4  # unit: None
        self.k_s2 = -2.167     # unit: None
        self.k_s3 = 1.408e-5  # unit: None
        self.k_s4 = 6.13 # unit: None
        self.E_a = 78.06  # unit: "kJ/mol"
        self.R = 8.314  # unit: "J/(k.mol)"
        self.T_ref = 298.15 # "unit": "K"
        self.T_i = 303.15   # "unit": "K"

    
    @property   
    def discharge_current_max(self):
        return self.discharge_current_max
    
    @discharge_current_max.setter
    def discharge_current_max(self, value):
        if value < 0:
            raise ValueError("discharge_current_max must be non-negative")
        self._discharge_current_max = value
        
    
    @property
    def charge_current_max(self):
        return self.charge_current_max
    
    @charge_current_max.setter
    def charge_current_max(self, value):
        if value < 0:
            raise ValueError("charge_current_max must be non-negative")
        self._charge_current_max = value
        
    
    @property
    def eol(self):
        return self.eol
    
    @eol.setter
    def eol(self, value):
        if (0 <= value <= 100):
            raise ValueError("End of life must must be between 0 and 100")
        self._eol = value
    
    @property
    def soc_min(self):
        return self.soc_min
    
    @soc_min.setter
    def soc_min(self, value):
        if (0 <= value <= 100): 
            raise ValueError("soc_min must be between 0 and 100")
        self._soc_min = value
    
    @property
    def soc_max(self):
        return self.soc_max
    
    @soc_max.setter
    def soc_max(self, value):
        if (0 <= value <= 100): 
            raise ValueError("soc_max must be between 0 and 100")
        self._soc_max = value
    
    @property
    def cell_nominal_capacity(self):
        return self.cell_nominal_capacity
    
    @cell_nominal_capacity.setter
    def cell_nominal_capacity(self, value):
        if value < 0:
            raise ValueError("cell_nominal_capacity must be non-negative")
        self._cell_nominal_capacity = value
    
    @property
    def internal_resistance(self):
        return self.internal_resistance
    
    @internal_resistance.setter
    def internal_resistance(self, value):
        if value < 0:
            raise ValueError("internal_resistance must be non-negative")
        self._internal_resistance = value
        
        
    @property
    def battery_charge_efficiency(self):
        return self.battery_charge_efficiency
    
    @property
    def battery_discharge_efficiency(self):
        return self.battery_discharge_efficiency
    
    @property
    def delta_dod(self):
        return self.delta_dod
    
    @property
    def cycle_life(self):
        return self.cycle_life
    
    @property
    def calendar_life(self):
        return self.calendar_life
    
    @property
    def power_max(self):
        return self.power_max   
    
    @property
    def current_max(self):
        return self.current_max
    
    @property
    def k_s1(self):
        return self.k_s1 
        
    @property
    def k_s2(self):
        return self.k_s2
    
    @property
    def k_s3(self):
        return self.k_s3
    
    @property
    def k_s4(self):
        return self.k_s4
    
    @property
    def E_a(self):
        return self.E_a
    
    @property
    def R(self):
        return self.R
    
    @property
    def T_ref(self):
        return self.T_ref
    
    @property
    def T_i(self):
        return self.T_i
    
    def _update_constants(self, new_constants):
            for key, value in new_constants.items():
                if hasattr(self, key): 
                    setattr(self, key, value)
                else:
                    raise AttributeError(f"{key} is not a valid constant in EnergyStorageModel")
    

    def _update_soc(self, action):
        if action == 1:
            self.soc += self.c_rate_charge
        elif action == 2:
            self.soc -= self.c_rate_discharge
        else:
            pass
        return self.soc
    
    def _update_soh(self, soc):
        if soc < self.soc_min:
            self.soh -= 1
        elif soc > self.soc_max:
            self.soh -= 1
        else:
            pass
        return self.soh
    
    
    

    
    
    def __repr__(self):
        return f"""Energy Storage Model Specifications:
        - Cell Voltage: {self.cell_voltage} V
        - Cell Stored Energy: {self.cell_stored_energy} Wh
        - Cell Nominal Capacity: {self.cell_nominal_capacity} Ah
        - Internal Resistance: {self.internal_resistance} mΩ
        - Battery charge Efficiency: {self.battery_charge_efficiency} %
        - Battery discharge Efficiency: {self.battery_discharge_efficiency} %
        - Continuous Discharge Current: {self.discharge_current_max} A
        - Continuous Charge Current: {self.charge_current_max} A
        - ΔDoD: {self.delta_dod} %
        - EoL: {self.eol} %
        - Cycle Life, 100% DOD: {self.cycle_life} Cycles
        - Calendar Life: {self.calendar_life} Years
        - SOC: {self.soc} %
        - SOH: {self.soh} %
        - SOC Min: {self.soc_min} %
        - SOC Max: {self.soc_max} %
        - Current Max: {self.current_max} A
        - Power Max: {self.power_max} W
        - Voltage Max: {self.voltage_max} V
        - Capacity : {self.capacity} kWh
        - soc inti: {self.soc_init} % 
        - c rate charge: {self.c_rate_charge} h-1
        - c rate discharge: {self.c_rate_discharge} h-1
        - cell series number: {self.cell_series} 
        - parallel branches : {self.parallel_branches} 
        - Ks1: {self.k_s1} 
        - Ks2: {self.k_s2} 
        - Ks3: {self.k_s3} 
        - Ks4: {self.k_s4} 
        - Ea: {self.E_a} kJ/mol
        - R : {self.R} J/(k.mol)
        - T ref: {self.T_ref} K
        - T init: {self.T_i} K """
        
if __name__ == "__main__":
    ess = EnergyStorageModel()
    print(ess)