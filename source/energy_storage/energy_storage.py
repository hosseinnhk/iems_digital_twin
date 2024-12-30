from scipy.integrate import quad
import numpy as np

class EnergyStorageModel:
    
    def __init__(self):
   
        super().__setattr__('_attributes', {})
        
        # single cell variables
        self.cell_voltage = 3.3  # Volts (V)
        self.cell_stored_energy = 3.63  # Watt-hour (Wh)
        self.cell_temperature = 25.0  # Temperature, in Celsius (°C)
        self.cell_capacity = 3.3  # Energy storage capacity (Wh)
        
        # battery pack variables
        self.state_of_charge = 30.0  # State of Charge, as a percentage
        self.state_of_health = 100.0  # State of Health, as a percentage
        self.voltage = 330.0  # Volts (V)
        self.current = 0.0  # Current, in Amps (A)
        self.state_of_power = 0.0  # Power, in Watts (W)
        self.available_energy = 0.0  # Energy, in Watt-hours (Wh)
        self.temperature = 25.0  # Temperature, in Celsius (°C)
        self.total_remained_capacity = 0.0  # Total Remained Capacity, in Ampere-hours (Ah)

        # constants for the model
        self._attributes.update({
            "time_resolution": 1.0,  # Time resolution, in seconds (s)
            "voltage_max": 340.0,  # Voltage, in Volts (V)
            "c_rate_charge": 1.0,  # Charge C-rate
            "c_rate_discharge": 1.0,  # Discharge C-rate
            "cell_series_number": 100,  # Number of cells in series
            "cell_parallel_number": 16,  # Number of parallel branches
            "state_of_health_init": 100.0,  # Initial State of Health, as a percentage
            "state_of_charge_init": 50.0,  # Initial State of Charge, as a percentage
            "discharge_current_max": 30.0,  # Amps (A)
            "charge_current_max": 4.0,  # Amps (A)
            "end_of_life": 70,  # Percentage (%) - End of Life criteria
            "state_of_charge_min": 15.0,  # Minimum State of Charge, as a percentage
            "state_of_charge_max": 90.0,  # Maximum State of Charge, as a percentage
            "cell_nominal_capacity": 1.1,  # Ampere-hour (Ah)
            "internal_resistance": 12.6,  # Milliohms (mΩ)
            "charge_efficiency": 0.96,  # Max 1
            "discharge_efficiency": 0.96,  # Max 1
            "delta_dod": 75.0,  # Percentage (%) - Depth of Discharge variation
            "cycle_life": 2000,  # Cycles for 100% Depth of Discharge (DOD)
            "calendar_life": 10.0,  # Years
            "power_max": 5000.0,  # Power, in Watts (W)
            "current_max": 30.0,  # Current, in Amps (A)
            "k_s1": -4.092e-4,  # Must be negative
            "k_s2": -2.167,  # Must be negative
            "k_s3": 1.408e-5,  # Must be non-negative
            "k_s4": 6.13,  # Must be non-negative
            "E_a": 78.06,  # kJ/mol
            "R": 8.314,  # J/(k.mol)
            "T_ref": 298.15,  # Kelvin
            "T_i": 303.15,  # Kelvin
        })

    def __getattr__(self, name):
        if name in self._attributes:
            return self._attributes[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Define validation rules dynamically
        validation_rules = {
            "time_resolution": lambda v: v >= 0,
            "voltage_max": lambda v: v >= 0,
            "c_rate_charge": lambda v: v >= 0,
            "c_rate_discharge": lambda v: v >= 0,
            "cell_series_number": lambda v: v >= 0,
            "cell_parallel_number": lambda v: v >= 0,
            "state_of_health_init": lambda v: 0 <= v <= 100,
            "state_of_charge_init": lambda v: 0 <= v <= 100,
            "discharge_current_max": lambda v: v >= 0,
            "charge_current_max": lambda v: v >= 0,
            "end_of_life": lambda v: 0 <= v <= 100,
            "state_of_charge_min": lambda v: 0 <= v <= 100,
            "state_of_charge_max": lambda v: 0 <= v <= 100,
            "cell_nominal_capacity": lambda v: v >= 0,
            "internal_resistance": lambda v: v >= 0,
            "charge_efficiency": lambda v: 0 <= v <= 1,
            "discharge_efficiency": lambda v: 0 <= v <= 1,
            "delta_dod": lambda v: 0 <= v <= 100,
            "cycle_life": lambda v: v >= 0,
            "calendar_life": lambda v: v >= 0,
            "power_max": lambda v: v >= 0,
            "current_max": lambda v: v >= 0,
            "k_s1": lambda v: v < 0,
            "k_s2": lambda v: v < 0,
            "k_s3": lambda v: v >= 0,
            "k_s4": lambda v: v >= 0,
            "E_a": lambda v: v >= 0,
            "R": lambda v: v >= 0,
            "T_ref": lambda v: v >= 0,
            "T_i": lambda v: v >= 0,
        }

        if name in validation_rules:
            if not validation_rules[name](value):
                raise ValueError(f"Invalid value for {name}: {value}")
            self._attributes[name] = value
        else:
            super().__setattr__(name, value)
            
            
    # def _update_constants(self, new_constants):
    #         for key, value in new_constants.items():
    #             if hasattr(self, key): 
    #                 setattr(self, key, value)
    #             else:
    #                 raise AttributeError(f"{key} is not a valid constant in EnergyStorageModel")
    
    def reset_to_initial_state(self):
        self.state_of_charge = self.state_of_charge_init
        self.state_of_health = self.state_of_health_init
        self.available_energy = self.cell_capacity * self.cell_series_number * self.cell_parallel_number * (self.state_of_charge / 100)
        self.temperature = self.cell_temperature
        
        
    def update_state_of_charge(self) -> None:
        """
        Updates the state of charge (SOC) of the battery based on the current, 
        time resolution, and total remaining capacity.
        
        This method modifies the `state_of_charge` attribute in place and does not return a value.
        """
        # Calculate the charge transferred during the time interval (Ah)
        charge_transferred = (self.time_resolution * self.current) / 3600
        
        # Update the state of charge
        self.state_of_charge += charge_transferred / self.total_remained_capacity
        
        # Clamp the state of charge within the allowed range
        self.state_of_charge = max(
            self.state_of_charge_min, 
            min(self.state_of_charge, self.state_of_charge_max)
        )
    

    def f_state_of_charge_avg(Qt_1, Qt, Qmax):
        
        delta_Qt = Qt - Qt_1
        state_of_charge_avg, _ = quad(lambda Q: f_state_of_charge(Q, Qmax), Qt_1, Qt)
        state_of_charge_avg = state_of_charge_avg / delta_Qt
        return state_of_charge_avg

    def f_state_of_charge_dev(Qt_1, Qt, Qmax):
        
        delta_Qt = Qt - Qt_1
        state_of_charge_avg = f_state_of_charge_avg(Qt_1, Qt, Qmax)
        integral_result, _ = quad(lambda Q: (f_state_of_charge(Q, Qmax) - state_of_charge_avg) ** 2, Qt_1, Qt)
        state_of_charge_dev = np.sqrt(abs((3 / delta_Qt) * integral_result))
        return state_of_charge_dev
    
    
    def calculate_total_remained_capacity(self):
        self.total_remained_capacity  = self.cell_series_number * self.cell_parallel_number * self.cell_nominal_capacity * self.state_of_health
        return self.total_remained_capacity
    
    def calculate_voltage(self):
        return (self.state_of_charge + 735) / 250
    
    def update_voltage(self):
        self.voltage = int(self.calculate_voltage() * 100)
    
    def update_available_energy(self):
        self.available_energy = self.cell_series_number * self.cell_parallel_number * self.cell_stored_energy * self.state_of_charge * self.state_of_health
        return self.available_energy
        
    def update_power(self):
        self.state_of_power = self.voltage * self.current
        return self.state_of_power
        
    def update_current(self):
        self.current = self.update_power(self) / self.voltage
    
    def update_temp(self, state_of_charge, state_of_health):
        self.temperature = self.cell_temperature * state_of_charge * state_of_health
        return self.temperature
    
    
    def f_Fi(ess, state_of_charge_dev, state_of_charge_avg):
        
        F = (ess.k_s1 * state_of_charge_dev * np.exp(ess.k_s2 * state_of_charge_avg) + ess.k_s3 * np.exp(ess.k_s4 * state_of_charge_dev))
        return F

    def f_c_cycle(F, Q, Ea, R, T, T_ref):

        c_cycle = sum(F[i] * abs(Q[i]-Q[i-1]) * np.exp(( -Ea / R ) * (1 / T - 1 / T_ref)) for i in range(len(F)))
        return c_cycle

    def f_c_cal_1h(state_of_charge_1h_avg):

        c_cal_1h = (6.6148 * state_of_charge_1h_avg + 4.6404) * 10**-6
        return c_cal_1h

    def f_c_cal(c_cal_1h_list):

        c_cal = sum(c_cal_1h_list)
        return c_cal

    def f_c_cycle_day(c_cycle_1h_list):

        c_cycle_day= sum(c_cycle_1h_list)
        return c_cycle_day

    def f_state_of_health(c_cal, c_cycel, c_nm):
        c_fd = c_cal + 100 * c_cycel/c_nm
        # state_of_health = 100 - c_fd
        return c_fd


    def state_of_health_daily_change(Qt, Qmax):
        
        c_cal_day = []
        c_cycle_day = []
        
        for i in range(int(len(Qt)/24)): # 0-23
            Fi = []
            Qi = []
            state_of_chargeAvg_1h = 0.0
            
            # first we calculate for each hour: 
            for j in range(12): # 0-11
                if i*12+j-1 > 0 : 
                    state_of_chargeAvg = f_state_of_charge_avg(Qt[i*12+j-1], Qt[i*12+j], Qmax)
                    state_of_chargeDev = f_state_of_charge_dev(Qt[i*12+j-1], Qt[i*12+j], Qmax)
                    Fi.append(f_Fi(state_of_chargeAvg, state_of_chargeDev))
                    Qi.append(Qt[i*12+j])
                    state_of_chargeAvg_1h += state_of_chargeAvg 
                    
            c_cycle_1h  = f_c_cycle(Fi, Qi, ess.E_a, ess.R, ess.T_i, ess.T_ref)
            c_cal_1h = f_c_cal_1h(state_of_chargeAvg_1h/12)
            c_cal_day.append(c_cal_1h)
            c_cycle_day.append(c_cycle_1h)
            
        c_cal = f_c_cal(c_cal_day)
        c_cycle = f_c_cycle_day(c_cycle_day)
        delta_state_of_health = f_state_of_health(c_cal, c_cycle, Qmax)       
        if delta_state_of_health< 0: 
            delta_state_of_health = 0
        return delta_state_of_health


    def update_state_of_health(self):
        self.state_of_health = self.state_of_health_init - self.state_of_health_daily_change(self.state_of_charge, self.cell_nominal_capacity)
        return self.state_of_health
    
    
    
    
    def __repr__(self):
        return f"""Energy Storage Model Specifications:
        - Cell Voltage: {self.cell_voltage} V
        - Cell Stored Energy: {self.cell_stored_energy} Wh
        - Cell Nominal Capacity: {self.cell_nominal_capacity} Ah
        - Internal Resistance: {self.internal_resistance} mΩ
        - Battery charge Efficiency: {self.charge_efficiency} %
        - Battery discharge Efficiency: {self.discharge_efficiency} %
        - Continuous Discharge Current: {self.discharge_current_max} A
        - Continuous Charge Current: {self.charge_current_max} A
        - ΔDoD: {self.delta_dod} %
        - End_of_life: {self.end_of_life} %
        - Cycle Life, 100% DOD: {self.cycle_life} Cycles
        - Calendar Life: {self.calendar_life} Years
        - state_of_charge: {self.state_of_charge} %
        - state_of_health: {self.state_of_health} %
        - state_of_charge Min: {self.state_of_charge_min} %
        - state_of_charge Max: {self.state_of_charge_max} %
        - Current Max: {self.current_max} A
        - Power Max: {self.power_max} W
        - Voltage Max: {self.voltage_max} V
        - Capacity : {self.cell_capacity} Wh
        - state_of_charge inti: {self.state_of_charge_init} % 
        - c rate charge: {self.c_rate_charge} h-1
        - c rate discharge: {self.c_rate_discharge} h-1
        - cell series number: {self.cell_series_number} 
        - parallel branches : {self.cell_parallel_number} 
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