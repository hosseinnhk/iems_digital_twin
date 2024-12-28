from scipy.integrate import quad
import numpy as np

class EnergyStorageModel:
    
    def __init__(self):
        
        # single cell specifications
        self.cell_voltage = 3.3  # Volts (V)
        self.cell_stored_energy = 3.63  # Watt-hour (Wh)
        self.cell_temperature = 25.0  # Temperature, in Celsius (°C)
        self.cell_capacity = 3.3 # energy storage capacity (Wh)
        
        # battery pack specifications
        self.state_of_charge = 30.0  # State of Charge, as a percentage
        self.state_of_health = 100.0 # State of Health, as a percentage
        self.voltage = 330.0  # Volts (V)
        self.current = 0.0 # Current, in Amps (A)
        self.state_of_power = 0.0 # Power, in Watts (W)
        self.available_energy = 0.0 # Energy, in Watt-hours (Wh)
        self.temperature = 25.0  # Temperature, in Celsius (°C)

        # constants for the model
        self._time_resolution = 1.0  # Time resolution, in seconds (s) 
        self._voltage_max = 340.0  # Voltage, in Volts (V)
        self._c_rate_charge = 1.0 # Charge  c rate
        self._c_rate_discharge = 1.0 # Discharge c rate
        self._cell_series_number = 100 # Number of cells in series
        self._cell_parallel_number = 16 # Number of parallel branches
        self._state_of_health_init = 100.0 # Initial State of Health, as a percentage
        self._state_of_charge_init = 50.0 # Initial State of Charge, as a percentage
        
        self._discharge_current_max = 30.0  # Amps (A)
        self._charge_current_max = 4.0  # Amps (A)
        self._end_of_life = 70  # Percentage (%) - End of Life criteria
        self._state_of_charge_min = 15.0 # Minimum State of Charge, as a percentage
        self._state_of_charge_max = 90.0 # Maximum State of Charge, as a percentage
        self._cell_nominal_capacity = 1.1  # Ampere-hour (Ah)
        self._internal_resistance = 12.6  # milliohms (mΩ)
        self._charge_efficiency = 0.96  # max 1
        self._discharge_efficiency = 0.96  # max 1
        self._delta_dod = 75.0  # Percentage (%) - Depth of Discharge variation
        self._cycle_life = 2000  # Cycles for 100% Depth of Discharge (DOD)
        self._calendar_life = 10.0  # Years
        self._power_max = 5000.0 # Power, in Watts (W)
        self._current_max = 30.0 # Current, in Amps (A)
        
        self._k_s1 =  -4.092e-4  # unit: None
        self._k_s2 = -2.167     # unit: None
        self._k_s3 = 1.408e-5  # unit: None
        self._k_s4 = 6.13 # unit: None
        self._E_a = 78.06  # unit: "kJ/mol"
        self._R = 8.314  # unit: "J/(k.mol)"
        self._T_ref = 298.15 # "unit": "K"
        self._T_i = 303.15   # "unit": "K"


    @property
    def time_resolution(self):
        return self._time_resolution
    
    @time_resolution.setter
    def time_resolution(self, value):
        if value < 0:
            raise ValueError("time_resolution must be non-negative")
        self._time_resolution = value
        
    @property
    def voltage_max(self):
        return self._voltage_max
    
    @voltage_max.setter
    def voltage_max(self, value):
        if value < 0:
            raise ValueError("voltage_max must be non-negative")
        self._voltage_max = value
        
    @property
    def c_rate_charge(self):
        return self._c_rate_charge
    
    @c_rate_charge.setter
    def c_rate_charge(self, value):
        if value < 0:
            raise ValueError("c_rate_charge must be non-negative")
        self._c_rate_charge = value
        
    @property
    def c_rate_discharge(self):
        return self._c_rate_discharge
    
    @c_rate_discharge.setter
    def c_rate_discharge(self, value):
        if value < 0:
            raise ValueError("c_rate_discharge must be non-negative")
        self._c_rate_discharge = value
        
    @property
    def cell_series_number(self):
        return self._cell_series_number
    
    @cell_series_number.setter
    def cell_series_number(self, value):
        if value < 0:
            raise ValueError("cell_series_number must be non-negative")
        self._cell_series_number = value
        
    @property
    def cell_parallel_number(self):
        return self._cell_parallel_number
    
    @cell_parallel_number.setter
    def cell_parallel_number(self, value):
        if value < 0:
            raise ValueError("cell_parallel_number must be non-negative")
        self._cell_parallel_number = value
        
    @property
    def state_of_health_init(self):
        return self._state_of_health_init
    
    @state_of_health_init.setter
    def state_of_health_init(self, value):
        if 0 <= value <= 100:
            self._state_of_health_init = value
        else:
            raise ValueError("state_of_health_init must be between 0 and 100")
        
    @property
    def state_of_charge_init(self):
        return self._state_of_charge_init
    
    @state_of_charge_init.setter
    def state_of_charge_init(self, value):
        if 0 <= value <= 100:
            self._state_of_charge_init = value
        else:
            raise ValueError("state_of_charge_init must be between 0 and 100")
    
    @property
    def discharge_current_max(self):
        return self._discharge_current_max

    @discharge_current_max.setter
    def discharge_current_max(self, value):
        if value < 0:
            raise ValueError("discharge_current_max must be non-negative")
        self._discharge_current_max = value
        
        
    @property
    def charge_current_max(self):
        return self._charge_current_max

    @charge_current_max.setter
    def charge_current_max(self, value):
        if value < 0:
            raise ValueError("charge_current_max must be non-negative")
        self._charge_current_max = value
    
    @property
    def end_of_life(self):
        return self._end_of_life

    @end_of_life.setter
    def end_of_life(self, value):
        if 0 <= value <= 100:
            self._end_of_life = value
        else:
            raise ValueError("end_of_life must be between 0 and 100")
        
    @property
    def state_of_charge_min(self):
        return self._state_of_charge_min

    @state_of_charge_min.setter
    def state_of_charge_min(self, value):
        if 0 <= value <= 100:
            self._state_of_charge_min = value
        else:
            raise ValueError("state_of_charge_min must be between 0 and 100")
    
    
    @property
    def state_of_charge_max(self):
        return self._state_of_charge_max

    @state_of_charge_max.setter
    def state_of_charge_max(self, value):
        if 0 <= value <= 100:
            self._state_of_charge_max = value
        else:
            raise ValueError("state_of_charge_max must be between 0 and 100")
    
    
    @property
    def cell_nominal_capacity(self):
        return self._cell_nominal_capacity

    @cell_nominal_capacity.setter
    def cell_nominal_capacity(self, value):
        if value < 0:
            raise ValueError("cell_nominal_capacity must be non-negative")
        self._cell_nominal_capacity = value
    
    
    @property
    def internal_resistance(self):
        return self._internal_resistance

    @internal_resistance.setter
    def internal_resistance(self, value):
        if value < 0:
            raise ValueError("internal_resistance must be non-negative")
        self._internal_resistance = value
        
        
    @property
    def charge_efficiency(self):
        return self._charge_efficiency

    @charge_efficiency.setter
    def charge_efficiency(self, value):
        if 0 <= value <= 1:
            self._charge_efficiency = value
        else:
            raise ValueError("charge_efficiency must be between 0 and 1")
    
    
    @property
    def discharge_efficiency(self):
        return self._discharge_efficiency

    @discharge_efficiency.setter
    def discharge_efficiency(self, value):
        if 0 <= value <= 1:
            self._discharge_efficiency = value
        else:
            raise ValueError("discharge_efficiency must be between 0 and 1")
    
    
    @property
    def delta_dod(self):
        return self._delta_dod

    @delta_dod.setter
    def delta_dod(self, value):
        if 0 <= value <= 100:
            self._delta_dod = value
        else:
            raise ValueError("delta_dod must be between 0 and 100")
    
    
    @property
    def cycle_life(self):
        return self._cycle_life

    @cycle_life.setter
    def cycle_life(self, value):
        if value < 0:
            raise ValueError("cycle_life must be non-negative")
        self._cycle_life = value
    
    @property
    def calendar_life(self):
        return self._calendar_life

    @calendar_life.setter
    def calendar_life(self, value):
        if value < 0:
            raise ValueError("calendar_life must be non-negative")
        self._calendar_life = value

    @property
    def power_max(self):
        return self._power_max

    @power_max.setter
    def power_max(self, value):
        if value < 0:
            raise ValueError("power_max must be non-negative")
        self._power_max = value
    
    
    @property
    def current_max(self):
        return self._current_max

    @current_max.setter
    def current_max(self, value):
        if value < 0:
            raise ValueError("current_max must be non-negative")
        self._current_max = value

    @property
    def k_s1(self):
        return self._k_s1

    @k_s1.setter
    def k_s1(self, value):
        if value >= 0:
            raise ValueError("k_s1 must be negative")
        self._k_s1 = value
        
        
    @property
    def k_s2(self):
        return self._k_s2

    @k_s2.setter
    def k_s2(self, value):
        if value >= 0:
            raise ValueError("k_s2 must be negative")
        self._k_s2 = value

    @property
    def k_s3(self):
        return self._k_s3

    @k_s3.setter
    def k_s3(self, value):
        if value < 0:
            raise ValueError("k_s3 must be non-negative")
        self._k_s3 = value

    @property
    def k_s4(self):
        return self._k_s4

    @k_s4.setter
    def k_s4(self, value):
        if value < 0:
            raise ValueError("k_s4 must be non-negative")
        self._k_s4 = value

    @property
    def E_a(self):
        return self._E_a

    @E_a.setter
    def E_a(self, value):
        if value < 0:
            raise ValueError("E_a must be non-negative")
        self._E_a = value

    @property
    def R(self):
        return self._R

    @R.setter
    def R(self, value):
        if value < 0:
            raise ValueError("R must be non-negative")
        self._R = value

    @property
    def T_ref(self):
        return self._T_ref

    @T_ref.setter
    def T_ref(self, value):
        if value < 0:
            raise ValueError("T_ref must be non-negative")
        self._T_ref = value

    @property
    def T_i(self):
        return self._T_i

    @T_i.setter
    def T_i(self, value):
        if value < 0:
            raise ValueError("T_i must be non-negative")
        self._T_i = value
        
    
    def _update_constants(self, new_constants):
            for key, value in new_constants.items():
                if hasattr(self, key): 
                    setattr(self, key, value)
                else:
                    raise AttributeError(f"{key} is not a valid constant in EnergyStorageModel")
    

    def update_state_of_charge(self, action):
        if action == 1:
            self.state_of_charge += self.c_rate_charge
        elif action == 2:
            self.state_of_charge -= self.c_rate_discharge
        else:
            pass
        # state_of_charge = Q / Qmax
        return self.state_of_charge
    
    def update_state_of_health(self, state_of_charge):
        if state_of_charge < self.state_of_charge_min:
            self.state_of_health -= 1
        elif state_of_charge > self.state_of_charge_max:
            self.state_of_health -= 1
        else:
            pass
        return self.state_of_health
    
    def calculate_voltage(self):
        return (self.state_of_charge + 735) / 250

    def update_voltage(self):
        self.voltage = int(self.calculate_voltage() * 100)
        
    def calculate_current(self):
        
    
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




    def f_state_of_charge(Q, Qmax):
        state_of_charge = Q / Qmax
        return state_of_charge

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