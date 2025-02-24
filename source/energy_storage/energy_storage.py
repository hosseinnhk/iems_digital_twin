import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Any
import pybamm
import logging
import random
import os


class EnergyStorageModel:
    
    def __init__(self):
   
        super().__setattr__('_attributes', {})
        super().__setattr__('_validation_rules', {
            "time_resolution [s]": lambda v: v > 0,  
            "nominal_voltage [v]": lambda v: v > 0,
            "nominal_cell_voltage [V]": lambda v: v > 0,
            "voltage_max [v]": lambda v: v > 0,
            "cell_voltage_max [v]": lambda v: v > 0,
            "voltage_min [v]": lambda v: v >= 0,
            "cell_voltage_min [v]": lambda v: v >= 0,
            "nominal_capacity [Ah]": lambda v: v > 0,
            "nominal_cell_capacity [Ah]": lambda v: v > 0,
            "power_max [w]": lambda v: v > 0,
            "cell_power_max [w]": lambda v: v > 0,
            "discharge_current_max [A]": lambda v: v > 0,
            "cell_discharge_current_max [A]": lambda v: v > 0,
            "charge_current_max [A]": lambda v: v > 0,
            "cell_charge_current_max [A]": lambda v: v > 0,
            
            # Common parameters
            "c_rate_charge_max": lambda v: v >= 0,
            "c_rate_discharge_max": lambda v: v >= 0,
            "cell_series_number [uint]": lambda v: isinstance(v, int) and v >= 1,
            "cell_parallel_number [uint]": lambda v: isinstance(v, int) and v >= 1,
            "total_number_of_cells [uint]": lambda v: isinstance(v, int) and v >= 1,
            "state_of_health_init [%]": lambda v: 0 <= v <= 100,
            "state_of_charge_init [%]": lambda v: 0 <= v <= 100,
            "end_of_life_point [%]": lambda v: 0 <= v <= 100,
            "state_of_charge_min [%]": lambda v: 0 <= v <= 100,
            "state_of_charge_max [%]": lambda v: 0 <= v <= 100,
            "charge_efficiency [%]": lambda v: 0 <= v <= 100,
            "discharge_efficiency [%]": lambda v: 0 <= v <= 100,
            "conctact_resistance [mΩ]": lambda v: v >= 0,
            "temperature_max [°C]": lambda v: -273.15 <= v,  # Absolute zero as the theoretical minimum
        })

        self.model = None
        self.parameter_values =  None
        self.state = None
        self.soh_param = None
    
        # single cell dynamic variables
        self._cell_state_of_charge = 0.0  # State of Charge, as a percentage
        self._cell_relative_state_of_charge = 0.0  # Relative State of Charge, as a percentage
        self._cell_state_of_health = 0.0  # State of Health, as a percentage
        self._cell_voltage = 0.0  # Volts (V)
        self._cell_current = 0.0  # Current, in Amps (A)
        self._cell_power = 0.0  # Power, in Watts (W)
        self._cell_state_of_power = 0.0  # Power/Power_max in percentage (%)
        self._cell_stored_energy = 0.0 # stored energy, in Watt-hours (Wh)
        self._cell_temperature = 0.0  # Temperature, in Celsius (°C)
        self._cell_remained_capacity= 0.0 # Cell capacity (Ah)

        # battery pack dynamic variables
        self._state_of_charge = 0.0  # State of Charge, as a percentage
        self._relative_state_of_charge = 0.0  # Relative State of Charge, as a percentage
        self._state_of_health = 0.0  # State of Health, as a percentage
        self._voltage = 0.0  # Volts (V)
        self.current = 0.0  # Current, in Amps (A)
        self.power = 0.0  # Power, in Watts (W)
        self._state_of_power = 0.0  # Power/Power_max in percentage (%)
        self._stored_energy = 0.0  # stored Energy, in Watt-hours (Wh)
        self._temperature = 0.0  # Temperature, in Celsius (°C)
        self._remained_capacity = 0.0  # Total Remained Capacity, in Ampere-hours (Ah)

        # constants for the model
        self._attributes.update({
            "time_resolution [s]": 1.0,  # Time resolution, in seconds (s)
            "nominal_voltage [v]": 340.0,  # Voltage, in Volts (V)
            "nominal_cell_voltage [V]": 3.63,  # Volts (V)  //pybamm
            "voltage_max [v]": 394.8,  # Voltage, in Volts (V)  
            "cell_voltage_max [v]": 4.2,  # Voltage, in Volts (V) //pybamm
            "voltage_min [v]": 235,  # Voltage, in Volts (V)
            "cell_voltage_min [v]": 2.5,  # Voltage, in Volts (V) //pybamm
            "nominal_capacity [Ah]": 30.0, # Ampere-hour (Ah)
            "nominal_cell_capacity [Ah]": 5.0,  # Ampere-hour (Ah) //pybamm
            "power_max [w]": 2000.0,  # Power, in Watts (W)
            "cell_power_max [w]": 3.55,  # Power, in Watts (W) 
            "discharge_current_max [A]": 6.0,  # Amps (A)
            "cell_discharge_current_max [A]": 1.0,  # Amps (A) 
            "charge_current_max [A]": 6.0,  # Amps (A)
            "cell_charge_current_max [A]": 1.0,  # Amps (A) 

            # common parameters
            "cell_model" : "DFN",
            "cell_chemistry": "Chen2020",
            "c_rate_charge_max": 0.2,  # Charge C-rate
            "c_rate_discharge_max": 0.2,  # Discharge C-rate
            "cell_series_number [uint]": 94,  # Number of cells in series
            "cell_parallel_number [uint]": 6,  # Number of parallel branches
            "total_number_of_cells [uint]": 564,  # Total number of cells
            "state_of_health_init [%]": 100.0,  # Initial State of Health, as a percentage
            "state_of_charge_init [%]": 50.0,  # Initial State of Charge, as a percentage
            "end_of_life_point [%]": 70.0,  # Percentage (%) - End of Life criteria
            "state_of_charge_min [%]": 15.0,  # Minimum State of Charge, as a percentage
            "state_of_charge_max [%]": 90.0,  # Maximum State of Charge, as a percentage
            "charge_efficiency [%]": 96.0,  # Max 100
            "discharge_efficiency [%]": 96.0,  # Max 100
            "conctact_resistance [mΩ]": 0.0,  # Milliohms (mΩ)
            "temperature_max [°C]": 60.0,  # Temperature, in Celsius (°C)
        })
        
    @property
    def cell_state_of_charge(self):
        return self._cell_state_of_charge

    @property
    def cell_relative_state_of_charge(self):
        return self._cell_relative_state_of_charge

    @property
    def cell_state_of_health(self):
        return self._cell_state_of_health

    @property
    def cell_voltage(self):
        return self._cell_voltage

    @property
    def cell_current(self):
        return self._cell_current

    @property
    def cell_power(self):
        return self._cell_power

    @property
    def cell_state_of_power(self):
        return self._cell_state_of_power

    @property
    def cell_stored_energy(self):
        return self._cell_stored_energy

    @property
    def cell_temperature(self):
        return self._cell_temperature

    @property
    def cell_remained_capacity(self):
        return self._cell_remained_capacity

    @property
    def state_of_charge(self):
        return self._state_of_charge

    @property
    def relative_state_of_charge(self):
        return self._relative_state_of_charge

    @property
    def state_of_health(self):
        return self._state_of_health

    @property
    def voltage(self):
        return self._voltage

    @property
    def state_of_power(self):
        return self._state_of_power

    @property
    def stored_energy(self):
        return self._stored_energy

    @property
    def temperature(self):
        return self._temperature

    @property
    def remained_capacity(self):
        return self._remained_capacity        
        
    def __getattr__(self, name):
        if name in self._attributes:
            return self._attributes[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        if name in self._validation_rules:
            if not self._validation_rules[name](value):
                raise ValueError(f"Invalid value for {name}: {value}")
            self._attributes[name] = value
        else:
            super().__setattr__(name, value)
       
    def __validate_parameter(self, key, value):
        if key in self._validation_rules:
            is_valid = self._validation_rules[key](value)
            if not is_valid:
                logging.warning(f"Invalid value for {key}: {value}. Using default or skipping update.")
                return False
        return True

    def __validate_input_parameters(self, parameters):

        excluded_parameters = [
            "cell_series_number [uint]", "cell_parallel_number [uint]", "voltage_max [v]", "voltage_min [v]", "total_number_of_cells [uint]",
            "voltage_max [v]", "cell_voltage_max [v]", "voltage_min [v]", "cell_voltage_min [v]", "nominal_cell_capacity [Ah]", "cell_power_max [w]", "cell_discharge_current_max [A]",
            "cell_charge_current_max [A]", "c_rate_charge_max", "c_rate_discharge_max", "state_of_health_init [%]", "end_of_life_point [%]", "conctact_resistance [mΩ]", "temperature_max [°C]"
        ]

        for key in parameters.keys():
            if key not in parameters and key not in excluded_parameters:
                raise KeyError(f"Missing required parameter: {key}")

            value = parameters[key]
            if not self.__validate_parameter(key, value):
                raise ValueError(f"Invalid value for {key}: {value}")

        logging.info("All parameters for initialization are valid")

    def initialize_pybamm_model(self, parameters: dict):   

        options = {
            "SEI": "solvent-diffusion limited",
            "SEI porosity change": "true",
            "lithium plating": "partially reversible",
            "lithium plating porosity change": "true",  # alias for "SEI porosity change"
            "particle mechanics": ("swelling and cracking", "swelling only"),
            "SEI on cracks": "true",
            "loss of active material": "stress-driven",
            "calculate discharge energy": "true",  # for compatibility with older PyBaMM versions
            "cell geometry": "pouch",
            "thermal": "lumped",
            "contact resistance": "true",
        }
        self.model = pybamm.lithium_ion.DFN(options)
        parameter_values = pybamm.ParameterValues("OKane2022")
        # parameter_values = pybamm.ParameterValues(parameters['cell_chemistry'])
        self.soh_param = pybamm.LithiumIonParameters()
        self.parameter_values = parameter_values
        self.var_pts = {
            "x_n": 5,  # negative electrode
            "x_s": 5,  # separator
            "x_p": 5,  # positive electrode
            "r_n": 30,  # negative particle
            "r_p": 30,  # positive particle
        }       
        self.__validate_input_parameters(parameters)
        
        A = self.parameter_values["Electrode width [m]"] * self.parameter_values["Electrode height [m]"]
        self.parameter_values["Cell cooling surface area [m2]"] = 2 * A
        self.parameter_values["Total heat transfer coefficient [W.m-2.K-1]"] = 5
         
        self._attributes["time_resolution [s]"] = parameters["time_resolution [s]"]
        self._attributes["state_of_charge_init [%]"] = parameters["state_of_charge_init [%]"]
        self._attributes["state_of_health_init [%]"] = parameters["state_of_health_init [%]"]
        
        self._cell_state_of_charge = self._state_of_charge = self._attributes.get("state_of_charge_init [%]", 50.0)      
        self._cell_state_of_health = self._state_of_health = self._attributes.get("state_of_health_init [%]", 100.0)
        
        self._attributes["nominal_capacity [Ah]"] = parameters["nominal_capacity [Ah]"] 
        self._attributes["nominal_voltage [v]"] = parameters["nominal_voltage [v]"]
        self._attributes["nominal_cell_voltage [V]"]= parameters["nominal_cell_voltage [V]"]

        parameter_values["Nominal cell capacity [A.h]"] = self._calculate_cell_nominal_capacity()
        self._attributes["nominal_cell_capacity [Ah]"] = parameter_values["Nominal cell capacity [A.h]"]
        self._attributes["cell_voltage_max [v]"] = parameter_values["Open-circuit voltage at 100% SOC [V]"]
        self._attributes["cell_voltage_min [v]"] = parameter_values["Open-circuit voltage at 0% SOC [V]"]
        
        self._temperature = self._cell_temperature = parameters["ambient_temperature [°C]"]

        self._attributes["cell_series_number [uint]"] = int(np.ceil(self._attributes["nominal_voltage [v]"]/ self._attributes["nominal_cell_voltage [V]"]))
        self._attributes["cell_parallel_number [uint]"] = int(np.ceil(self._attributes["nominal_capacity [Ah]"] / self._attributes["nominal_cell_capacity [Ah]"]))
        
        self._attributes["nominal_capacity [Ah]"] = self._attributes["nominal_cell_capacity [Ah]"] * self._attributes["cell_parallel_number [uint]"] 
        self._attributes["nominal_voltage [V]"] = self._attributes["nominal_cell_voltage [V]"] * self._attributes["cell_series_number [uint]"]
        
        self._attributes["voltage_max [v]"] = self._attributes["cell_voltage_max [v]"] * self._attributes["cell_series_number [uint]"]
        self._attributes["voltage_min [v]"] = self._attributes["cell_voltage_min [v]"] * self._attributes["cell_series_number [uint]"]
        
        # parameter_values["Number of cells connected in series to make a battery"] = self._attributes["cell_series_number [uint]"]
        # parameter_values["Number of electrodes connected in parallel to make a cell"] = self._attributes["cell_parallel_number [uint]"] 
        parameter_values["Number of cells connected in series to make a battery"] = 1 # simulate a single cell
        parameter_values["Number of electrodes connected in parallel to make a cell"] = 1 # simulate a single cell
        self._attributes["total_number_of_cells [uint]"] = self._attributes["cell_series_number [uint]"] * self._attributes["cell_parallel_number [uint]"]
        
        self.current = parameters["current [A]"]
        self._cell_current  = self.current / self._attributes["cell_parallel_number [uint]"] 
        
        parameter_values["Ambient temperature [K]"] = parameters["ambient_temperature [°C]"] + 273.15
        parameter_values["Initial temperature [K]"] = parameters["ambient_temperature [°C]"] + 273.15
        parameter_values['Current function [A]' ] = self._cell_current
        
        # sim = pybamm.Simulation(self.model, parameter_values=parameter_values, var_pts=self.var_pts)
        # sol = sim.solve([0,1], initial_soc=self._attributes["state_of_charge_init [%]"]/100)
        # self._cell_voltage = sol["Terminal voltage [V]"].data[-1]
        self._voltage = self._cell_voltage * self._attributes["cell_series_number [uint]"]
        
        self._cell_power = self._cell_current * self._cell_voltage # Power, in Watts (W)
        self.power = self._cell_power * self._attributes["total_number_of_cells [uint]"] # Power, in Watts (W)
        
        self._attributes["power_max [w]"] = parameters["power_max [w]"]
        self._attributes["cell_power_max [w]"] = round(self._attributes["power_max [w]"] / self._attributes["total_number_of_cells [uint]"], 2)
        
        self._cell_state_of_power = self._cell_power / self._attributes["cell_power_max [w]"]  # Power/Power_max in percentage (%)
        self._state_of_power = self._cell_state_of_power
        
        self._cell_remained_capacity= self._attributes["nominal_cell_capacity [Ah]"] * (self._attributes["state_of_health_init [%]"] / 100)  # Ah
        self._remained_capacity = self._cell_remained_capacity * self._attributes["total_number_of_cells [uint]"]  # Ah
        
        self._cell_stored_energy = self._cell_remained_capacity * self._cell_voltage * (self._attributes["state_of_charge_init [%]"] / 100)  # Wh
        self._stored_energy = self._cell_stored_energy * self._attributes["total_number_of_cells [uint]"]  # Wh
        
        self._attributes["discharge_current_max [A]"] = parameters["discharge_current_max [A]"]
        self._attributes["cell_discharge_current_max [A]"] = round(self._attributes["discharge_current_max [A]"] / self._attributes["cell_parallel_number [uint]"],2)
        self._attributes["charge_current_max [A]"] = parameters["charge_current_max [A]"]
        self._attributes["cell_charge_current_max [A]"] = round(self._attributes["charge_current_max [A]"] / self._attributes["cell_parallel_number [uint]"],2)
        
        self._attributes["end_of_life_point [%]"] = parameters["end_of_life_point [%]"]
        self._attributes["state_of_charge_min [%]"] = parameters["state_of_charge_min [%]"]
        self._attributes["state_of_charge_max [%]"] = parameters["state_of_charge_max [%]"]
        self._attributes["charge_efficiency [%]"] = parameters["charge_efficiency [%]"]
        self._attributes["discharge_efficiency [%]"] = parameters["discharge_efficiency [%]"]
        self._attributes["temperature_max [°C]"] = parameters["temperature_max [°C]"]
        
        self._attributes["conctact_resistance [mΩ]"] = parameter_values["Contact resistance [Ohm]"] * 1000
        self._attributes["c_rate_charge_max"] = parameters["c_rate_charge_max"]
        self._attributes["c_rate_discharge_max"] = parameters["c_rate_discharge_max"]
        
        self.parameter_values = parameter_values
        
        # for key in self._validation_rules:
        #     value = self._attributes[key]
        #     if not (self.__validate_parameter(key, value)):
        #         raise ValueError(f"Invalid value for {key}: {value}")
        # logging.info("All parameters are intialized and validated")
    
    def run_model(self, current:float, ambient_temp:float, time_duration: int, previous_state=None) -> tuple[bool, list]:

        try:
            current_state  = self.__run_simulation(current, ambient_temp, time_duration, state=previous_state)
            self.__update_params(current_state)
            current_state = current_state.cycles[-1]
            # current_state = current_state
            # self.__validate_operation()
            return False, current_state
        except Exception as e:
            print(f"Battery storage simulation failed")
            return True, previous_state

    def __run_simulation(self, current:float, ambient_temp:float, time_duration: int, state = None) -> list:
        self.parameter_values["Current function [A]"] = current/self._attributes["cell_parallel_number [uint]"]
        self.parameter_values["Ambient temperature [K]"] = ambient_temp + 273.15
        
        if current < 0:
            self.experiment =pybamm.Experiment([f"Discharge at {(np.abs(current)/self._attributes["cell_parallel_number [uint]"])} A for {time_duration} seconds"])
        elif current > 0:
            self.experiment =pybamm.Experiment([f"Charge at {(current/self._attributes["cell_parallel_number [uint]"])} A for {time_duration} seconds"])
        else:
            self.experiment =pybamm.Experiment([f"Rest for {time_duration} seconds"])
            

        sim = pybamm.Simulation(self.model, experiment= self.experiment, parameter_values=self.parameter_values, var_pts=self.var_pts)
        solution = sim.solve(starting_solution=state)
        return solution
        
    def __update_params(self, solution) -> None:
        # solution = solutions[-1]
        self._voltage = solution["Battery voltage [V]"].data[-1] * self._attributes["cell_series_number [uint]"]
        self._cell_voltage = solution["Voltage [V]"].data[-1]
        self._cell_current = solution["Current [A]"].data[-1]
        self.current = self._cell_current * self._attributes["cell_parallel_number [uint]"]
        self._cell_power = solution["Power [W]"].data[-1]
        self.power = self._cell_power * self._attributes["total_number_of_cells [uint]"]
        # self._temperature = self._cell_temperature = solution["Cell temperature [C]"].data[-1]
        self._temperature = self._cell_temperature = solution["X-averaged cell temperature [K]" ].data[-1] - 273.15
        self._state_of_charge = self._cell_state_of_charge = self.__update_state_of_charge(solution)
        self._state_of_health = self._cell_state_of_health = self.__update_state_of_health(solution)
        self._cell_remained_capacity= self.__update_remained_capacity()
        self._remained_capacity = self._cell_remained_capacity * self._attributes["cell_parallel_number [uint]"]
        self._cell_stored_energy = self.__update_cell_stored_energy()
        self._stored_energy = self._cell_stored_energy * self._attributes["total_number_of_cells [uint]"]
        self._state_of_power = self._cell_state_of_power = self.__update_state_of_power()
 
    def __update_state_of_charge(self, solution) -> float:
        soc_init = self._attributes["state_of_charge_init [%]"]
        delta_discharge_capacity = solution["Discharge capacity [A.h]"].data[0] - solution["Discharge capacity [A.h]"].data[-1]  
        soc_variation = delta_discharge_capacity / (self._cell_remained_capacity) * 100 # considering the state of health and capacity fading effect
        soc = soc_init + soc_variation
        self._relative_state_of_charge = self.__calculate_relative_soc(soc)
        return soc

    def __calculate_relative_soc(self, soc) -> float:
        """ 
        Calculate the relative state of charge of the battery.
        based on soc min and soc max
        """
        soc_relative =  (soc - self._attributes["state_of_charge_min [%]"]) / (self._attributes["state_of_charge_max [%]"] - self._attributes["state_of_charge_min [%]"]) * 100
        return soc_relative

    def _calculate_cell_nominal_capacity(self):
        Q_n = self.parameter_values.evaluate(self.soh_param.n.Q_init)
        Q_p = self.parameter_values.evaluate(self.soh_param.p.Q_init)
        Q_Li = self.parameter_values.evaluate(self.soh_param.Q_Li_particles_init)
        esoh_solver = pybamm.lithium_ion.ElectrodeSOHSolver(self.parameter_values, self.soh_param)
        inputs = {"Q_n": Q_n, "Q_p": Q_p, "Q_Li": Q_Li}    # check if voltage is needed or not
        # inputs = {"V_min": Vmin, "V_max": Vmax, "Q_n": Q_n, "Q_p": Q_p, "Q_Li": Q_Li}
        esoh_sol = esoh_solver.solve(inputs)
        return esoh_sol["Q"]
        
    def __update_state_of_health(self, solution) -> float:
        """
        Calculate the State of Health (SOH) of a battery.

        Returns:
        float: SOH value in percentage.
        """
        # method 1
        # soh_init = self._cell_state_of_health
        # Qt_initial = self._cell_remained_capacity


        # Q_sei = solution["Loss of capacity to negative SEI [A.h]"].data[0] - solution["Loss of capacity to negative SEI [A.h]"].data[-1]
        # Q_sei_cr = solution["Loss of capacity to negative SEI on cracks [A.h]"].data[0] - solution["Loss of capacity to negative SEI on cracks [A.h]"].data[-1]
        # Q_plating = solution["Loss of capacity to negative lithium plating [A.h]"].data[0] - solution["Loss of capacity to negative lithium plating [A.h]"].data[-1]
        # Q_side = solution["Total capacity lost to side reactions [A.h]"].data[0] - solution["Total capacity lost to side reactions [A.h]"].data[-1]
        # Q_side = solution["Total capacity lost to side reactions [A.h]"].data[-1]
        
        
        
        # Q_sei = solution["Loss of capacity to negative SEI [A.h]"].data[-1]
        # Q_sei_cr =  solution["Loss of capacity to negative SEI on cracks [A.h]"].data[-1]
        # Q_plating = solution["Loss of capacity to negative lithium plating [A.h]"].data[-1]
        # Q_side = solution["Total capacity lost to side reactions [A.h]"].data[-1]
        # Q_side = solution["Total capacity lost to side reactions [A.h]"].data[-1]
        # Q_lli = (
        #             (solution["Total lithium lost [mol]"].data[0] - solution["Total lithium lost [mol]"].data[-1]) * 96485.3 / 3600
        # )  # mol to A.h

        # Q_lost = Q_sei + Q_sei_cr + Q_plating + Q_side + Q_lli
        # soh_lost= -(Q_lost / Qt_initial) * 100 # %
        # soh = soh_init - soh_lost
        
        # # method 2
        # cell_capacity = solution.summery_variables["Capacity [A.h]"]
        # cell_capacity = solution["Discharge capacity [A.h]"].data[-1]
        # soh = cell_capacity / self._attributes["nominal_cell_capacity [Ah]"] * 100
        

        Vmin = self._attributes["cell_voltage_min [v]"]
        Vmax = self._attributes["cell_voltage_max [v]"]
        Q_n = solution["Negative electrode capacity [A.h]"].data[-1]
        Q_p = solution["Positive electrode capacity [A.h]"].data[-1]
        Q_Li = solution["Total lithium capacity in particles [A.h]"].data[-1]     
        esoh_solver = pybamm.lithium_ion.ElectrodeSOHSolver(self.parameter_values, self.soh_param)

        inputs = {"Q_n": Q_n, "Q_p": Q_p, "Q_Li": Q_Li}    # check if voltage is needed or not
        # inputs = {"V_min": Vmin, "V_max": Vmax, "Q_n": Q_n, "Q_p": Q_p, "Q_Li": Q_Li}
        esoh_sol = esoh_solver.solve(inputs)

        # for var in ["x_100", "y_100", "Q", "x_0", "y_0"]:
        #     print(var, ":", esoh_sol[var])
        # print("Q:", esoh_sol["Q"])
        soh = (esoh_sol["Q"] / self._attributes["nominal_cell_capacity [Ah]"]) * 100
        return soh
 
    def __update_remained_capacity(self):
        remianed_capacity = self._attributes["nominal_cell_capacity [Ah]"]  * (self._cell_state_of_health/100) # Ah
        return  remianed_capacity 

    def __update_cell_stored_energy(self):
        
        cell_stored_energy = self._cell_remained_capacity * self._cell_voltage * (self._cell_state_of_charge / 100)  # Wh
        return cell_stored_energy  
        
    def __update_state_of_power(self) -> None:
        """
        Updates the state of power of the battery based on the power.
        
        This method modifies the `state_of_power` attribute in place and does not return a value.
        """
        cell_state_of_power = None 
        return cell_state_of_power
    
    def __update_cycles_count(self):
        self.number_of_cycles += 1

    def __validate_operation(self):
        """
        Validates the dynamic parmateters range during operation against the specified constraints.
        
        Raises:
            ValueError: If any of the constraints are violated.
        """
        
        if not (self.state_of_charge_min <= self._state_of_charge <= self.state_of_charge_max):
            raise ValueError("State of Charge out of bounds")
        if not (self._voltage_min <= self._voltage <= self._voltage_max):
            raise ValueError("Voltage out of bounds")
        if not ( 0<= self._temperature <= 60): 
            raise ValueError("Overheating detected")
        if not (self.power <= self.power_max):
            raise ValueError("Power out of bounds")
        if not (abs(self.current) <= self.current_max):
            raise ValueError("Current out of bounds")
        if not ( 0 <= self._state_of_power <= 1):
            raise ValueError("State of Power out of bounds")
        if not (0 <= self._stored_energy <= self.nominal_capacity * self._voltage_max):
            raise(ValueError("Stored Energy out of bounds"))
        if not (0 <= self._remained_capacity <= self.nominal_capacity):
            raise(ValueError("Remained Capacity out of bounds"))
        if not (0 <= self._state_of_health <= 100):
            raise(ValueError("State of Health out of bounds"))
        if (self._state_of_health <= self.end_of_life):
            raise(ValueError("End of Life reached"))

    def reset_to_initial_state(self)-> None:
        """
        Resets the battery to its initial state.
        """
        return True

    def report_state(self) -> dict:  
        state_dict = {
            "cell_voltage": (round(self._cell_voltage, 2), "V"),
            "cell_current": (round(self._cell_current, 2), "A"),
            "voltage": (round(self._voltage, 2), "V"),
            "current": (round(self.current, 2), "A"),
            "state_of_charge": (round(self._state_of_charge, 2), "%"),
            "relative_state_of_charge": (round(self._relative_state_of_charge, 2), "%"),
            "state_of_health": (round(self._state_of_health, 2), "%"),
            "power": (round(self.power, 2), "W"),
            # "state_of_power": (round(self._state_of_power, 2), "%"),
            "stored_energy": (round(self._stored_energy, 2), "Wh"),
            "temperature": (round(self._temperature, 2), "°C"),
            "remained_capacity": (round(self._remained_capacity, 2), "Ah"),
            "cell remaining capacity": (round(self._cell_remained_capacity, 2), "Ah"),
            # "total number of cells": (self._attributes["total_number_of_cells [uint]"], "cells"),
            # "Number of series cells": (self._attributes["cell_series_number [uint]"], "cells"),
            # "Number of parallel cells": (self._attributes["cell_parallel_number [uint]"], "cells"),
            }
        return state_dict
    
    def dynamic_plot(sellf, state):
        plt.style.use("seaborn-v0_8-deep")
        pybamm.settings.max_words_in_line = 3
        pybamm.dynamic_plot(state)
          
    def plot_results(self, results, plot_params: dict, save_plot=False) -> None:
        """
        Generate plots based on the given plot parameters.

        Args:
            results (list): A list of dictionaries containing data for plotting.
            plot_parameters (list): A list of parameter names to plot.
                Example:
                ["state_of_charge", "state_of_health", "current", "temperature"]
        """
        x_steps = list(range(len(results)))

        data = {key: [result[key][0] for result in results] for key in plot_params}

        num_plots = len(plot_params)

        if num_plots > 1:
            fig, axs = plt.subplots(num_plots, 1, figsize=(6, 3 * num_plots))
            axs = axs if isinstance(axs, (list, np.ndarray)) else [axs]
        else:
            fig, axs = plt.subplots(figsize=(6, 4))
            axs = [axs]

        fig.suptitle("Battery Parameters Over Time", fontsize=12)

        for ax, key in zip(axs, plot_params):
            random_color = "#" + "".join([random.choice("0123456789ABCDEF") for _ in range(6)])
            label = key.replace("_", " ").title()
            ax.plot(x_steps, data[key], label=label, color=random_color)
            # ax.set_title(label)
            ax.set_xlabel("Time Steps")
            unit = self._select_unit(label)
            label = f"{label} ({unit})"
            ax.set_ylabel(label)
            ax.grid(True)
            ax.legend()

        if save_plot:
            output_dir = "figures"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            timestamp = datetime.now().strftime("%m%d_%H%M%S")
            filename = f"{output_dir}/plot_{'_'.join(plot_params)}_{timestamp}.png"
            plt.savefig(filename)
            print(f"Figure saved as {filename}")

        # plt.tight_layout()
        # plt.show()      

    def _select_unit(self, label: str) -> str:            
        if "Voltage" in label:
            return "V"
        elif "Current" in label:
            return "A"
        elif "Power" in label:
            return "W"
        elif "Energy" in label:
            return "Wh"
        elif "capacity" in label:
            return "Ah"
        elif "Temperature" in label:
            return "°C"
        elif "State" in label:
            return "%"         
        else:
            return ""
        
         
    def __repr__(self):
        return f"""Energy Storage Model Specifications:
        - Cell Voltage: {self._cell_voltage} V
        - Cell Stored Energy: {self._cell_stored_energy} Wh
        - Cell Nominal Capacity: {self._attributes["nominal_cell_capacity [Ah]"]} Ah
        - Cell Internal Resistance: {self._attributes["conctact_resistance [mΩ]"]} mΩ
        - Battery charge Efficiency: {self._attributes["charge_efficiency [%]"]} %
        - Battery discharge Efficiency: {self._attributes["discharge_efficiency [%]"]} %
        - Continuous Discharge Current: {self._attributes["discharge_current_max [A]"]} A
        - Continuous Charge Current: {self._attributes["charge_current_max [A]"]} A
        - End_of_life: {self._attributes["end_of_life_point [%]"]} %
        - state_of_charge: {self._state_of_charge} %
        - relative_state_of_charge: {self._relative_state_of_charge} %
        - state_of_health: {self._state_of_health} %
        - state_of_charge Min: {self._attributes["state_of_charge_min [%]"]} %
        - state_of_charge Max: {self._attributes["state_of_charge_max [%]"]} %
        - Current Max: {self._attributes["discharge_current_max [A]"]} A
        - Power Max: {self._attributes["power_max [w]"]} W
        - Voltage Max: {self._attributes["voltage_max [v]"]} V
        - Voltage Min: {self._attributes["voltage_min [v]"]} V
        - Capacity: {self._attributes["nominal_capacity [Ah]"]} Ah
        - state_of_charge init: {self._attributes["state_of_charge_init [%]"]} %
        - state_of_health init: {self._attributes["state_of_health_init [%]"]} %
        - c rate charge: {self._attributes["c_rate_charge_max"]} h-1
        - c rate discharge: {self._attributes["c_rate_discharge_max"]} h-1
        - cell series number: {self._attributes["cell_series_number [uint]"]} 
        - parallel branches: {self._attributes["cell_parallel_number [uint]"]}"""

if __name__ == "__main__":
    ess = EnergyStorageModel()
    print(ess)