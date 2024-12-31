from scipy.integrate import quad
import numpy as np
from datetime import datetime
from typing import Any
import pybamm
import logging

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
    
        # single cell dynamic variables
        self.cell_state_of_charge = 0.0  # State of Charge, as a percentage
        self.cell_state_of_health = 0.0  # State of Health, as a percentage
        self.cell_voltage = 0.0  # Volts (V
        self.cell_current = 0.0  # Current, in Amps (A)
        self.cell_power = 0.0  # Power, in Watts (W)
        self.cell_state_of_power = 0.0  # Power/Power_max in percentage (%)
        self.cell_stored_energy = 0.0 # stored energy, in Watt-hours (Wh)
        self.cell_temperature = 0.0  # Temperature, in Celsius (°C)
        self.cell_remained_capacity = 0.0 # Cell capacity (Ah)

        # battery pack dynamic variables
        self.state_of_charge = 0.0  # State of Charge, as a percentage
        self.state_of_health = 0.0  # State of Health, as a percentage
        self.voltage = 0.0  # Volts (V)
        self.current = 0.0  # Current, in Amps (A)
        self.power = 0.0  # Power, in Watts (W)
        self.state_of_power = 0.0  # Power/Power_max in percentage (%)
        self.stored_energy = 0.0  # stored Energy, in Watt-hours (Wh)
        self.temperature = 0.0  # Temperature, in Celsius (°C)
        self.remained_capacity = 0.0  # Total Remained Capacity, in Ampere-hours (Ah)

        # constants for the model
        self._attributes.update({
            "time_resolution [s]": 1.0,  # Time resolution, in seconds (s)
            "nominal_voltage [v]": 340.0,  # Voltage, in Volts (V)
            "nominal_cell_voltage [V]": 3.63,  # Volts (V)
            "voltage_max [v]": 394.8,  # Voltage, in Volts (V)
            "cell_voltage_max [v]": 4.2,  # Voltage, in Volts (V)
            "voltage_min [v]": 235,  # Voltage, in Volts (V)
            "cell_voltage_min [v]": 2.5,  # Voltage, in Volts (V)
            "nominal_capacity [Ah]": 30.0, # Ampere-hour (Ah)
            "nominal_cell_capacity [Ah]": 5.0,  # Ampere-hour (Ah)
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
        """
        Validates a single parameter using the validation rules.
        Logs a warning if the parameter is invalid.
        """
        if key in self._validation_rules:
            is_valid = self._validation_rules[key](value)
            if not is_valid:
                logging.warning(f"Invalid value for {key}: {value}. Using default or skipping update.")
                return False
        return True

    def initialize_pybamm_model(self, parameters: dict):   
        """
        Initializes the PyBaMM model for the battery.
        
        Returns:
            pybamm.Model: The PyBaMM model for the battery.
            parameters: The parameter set to use for the PyBaMM model.
        """
        self.model = pybamm.lithium_ion.DFN()      
        parameters_value = pybamm.ParameterValues(parameters['cell_chemistry'])
        
        excluded_parameters = ["cell_series_number [uint]", "cell_parallel_number [uint]", "voltage_max [v]", "voltage_min [v]", "total_number_of_cells [uint]", 
            "voltage_max [v]", "cell_voltage_max [v]", "voltage_min [v]", "cell_voltage_min [v]", "nominal_cell_capacity [Ah]", "cell_power_max [w]", "cell_discharge_current_max [A]",
            "cell_charge_current_max [A]", "c_rate_charge_max", "c_rate_discharge_max","state_of_health_init [%]","end_of_life_point [%]", "conctact_resistance [mΩ]", "temperature_max [°C]"]
        
        for key in parameters.keys():
            if key not in parameters and key not in excluded_parameters:
                raise KeyError(f"Missing required parameter: {key}")
            
            value = parameters[key]
            if not (self.__validate_parameter(key, value)):
                raise ValueError(f"Invalid value for {key}: {value}")
            
        logging.info("All parameters for initialization are valid")
        
        self._attributes["time_resolution [s]"] = parameters["time_resolution [s]"]
        self._attributes["state_of_charge_init [%]"] = parameters["state_of_charge_init [%]"]
        self._attributes["state_of_health_init [%]"] = parameters["state_of_health_init [%]"]
        
        self.cell_state_of_charge = self.state_of_charge = self._attributes.get("state_of_charge_init [%]", 50.0)      
        self.cell_state_of_health = self.state_of_health = self._attributes.get("state_of_health_init [%]", 100.0)
        
        self._attributes["nominal_capacity [Ah]"] = parameters["nominal_capacity [Ah]"] 
        self._attributes["nominal_voltage [v]"] = parameters["nominal_voltage [v]"]
        self._attributes["nominal_cell_voltage [V]"]= parameters["nominal_cell_voltage [V]"]

        
        self._attributes["nominal_cell_capacity [Ah]"] = parameters_value["Nominal cell capacity [A.h]"]
        self._attributes["cell_voltage_max [v]"] = parameters_value["Upper voltage cut-off [V]"]
        self._attributes["cell_voltage_min [v]"] = parameters_value["Lower voltage cut-off [V]"]
        
        self.cell_temperature = parameters["ambient_temperature [°C]"]
        self.temperature = self.cell_temperature

        self._attributes["cell_series_number [uint]"] = int(np.ceil(self._attributes["nominal_voltage [v]"]/ self._attributes["nominal_cell_voltage [V]"]))
        self._attributes["cell_parallel_number [uint]"] = int(np.ceil(self._attributes["nominal_capacity [Ah]"] / self._attributes["nominal_cell_capacity [Ah]"]))
        

        self._attributes["nominal_capacity [Ah]"] = self._attributes["nominal_cell_capacity [Ah]"] * self._attributes["cell_parallel_number [uint]"] 
        self._attributes["nominal_voltage [V]"] = self._attributes["nominal_cell_voltage [V]"] * self._attributes["cell_series_number [uint]"]
        
        self._attributes["voltage_max [v]"] = self._attributes["cell_voltage_max [v]"] * self._attributes["cell_series_number [uint]"]
        self._attributes["voltage_min [v]"] = self._attributes["cell_voltage_min [v]"] * self._attributes["cell_series_number [uint]"]
        

        parameters_value["Number of cells connected in series to make a battery"] = self._attributes["cell_series_number [uint]"]
        parameters_value["Number of electrodes connected in parallel to make a cell"] = self._attributes["cell_parallel_number [uint]"] 
        self._attributes["total_number_of_cells [uint]"] = self._attributes["cell_series_number [uint]"] * self._attributes["cell_parallel_number [uint]"]
        
        self.current = parameters["current [A]"]
        self.cell_current  = self.current / self._attributes["cell_parallel_number [uint]"] 
        
        
        parameters_value["Ambient temperature [K]"] = parameters["ambient_temperature [°C]"] + 273.15
        parameters_value["Initial temperature [K]"] = parameters["ambient_temperature [°C]"] + 273.15
        parameters_value['Current function [A]' ] = self.cell_current
        
        sim = pybamm.Simulation(self.model, parameter_values=parameters_value)
        sim.solve([0, 1])
        
        self.cell_voltage = sim.solution["Terminal voltage [V]"](1)
        self.voltage = self.cell_voltage * self._attributes["cell_series_number [uint]"]
        
      
        self.cell_power = self.cell_current * self.cell_voltage # Power, in Watts (W)
        self.power = self.cell_power * self._attributes["total_number_of_cells [uint]"] # Power, in Watts (W)
        
        self._attributes["power_max [w]"] = parameters["power_max [w]"]
        self._attributes["cell_power_max [w]"] = round(self._attributes["power_max [w]"] / self._attributes["total_number_of_cells [uint]"], 2)
        
        
        self.cell_state_of_power = self.cell_power / self._attributes["cell_power_max [w]"]  # Power/Power_max in percentage (%)
        self.state_of_power = self.cell_state_of_power
        
        self.cell_remained_capacity = self._attributes["nominal_cell_capacity [Ah]"] * (self._attributes["state_of_health_init [%]"] / 100)  # Ah
        self.remained_capacity = self.cell_remained_capacity * self._attributes["total_number_of_cells [uint]"]  # Ah
        
        self.cell_stored_energy = self.cell_remained_capacity * self.cell_voltage * (self._attributes["state_of_charge_init [%]"] / 100)  # Wh
        self.stored_energy = self.cell_stored_energy * self._attributes["total_number_of_cells [uint]"]  # Wh
        
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
        
        self._attributes["conctact_resistance [mΩ]"] = parameters_value["Contact resistance [Ohm]"] * 1000
        self._attributes["c_rate_charge_max"] = parameters["c_rate_charge_max"]
        self._attributes["c_rate_discharge_max"] = parameters["c_rate_discharge_max"]
        
        
        for key in self._validation_rules:
        
            value = self._attributes[key]
            # print(f"{key} : {value}")
            if not (self.__validate_parameter(key, value)):
                raise ValueError(f"Invalid value for {key}: {value}")
        logging.info("All parameters are intialized and validated")
        
        return self.model, parameters_value
    
     
    def update_constants_batch(self, new_constants: dict)-> None:
        """
        Updates the constants of the battery model.
        
        Args:
            new_constants (dict): A dictionary of new constants.
            
        Raises:
            AttributeError: If the constant is not valid.
            ValueError: If the value of the constant is invalid
        """
        for key, value in new_constants.items():
            if key not in self._validation_rules:
                raise AttributeError(f"{key} is not a valid constant in EnergyStorageModel")
            if not self.validation_rules[key](value):
                raise ValueError(f"Invalid value for {key}: {value}")
        
        for key, value in new_constants.items():
            self._attributes[key] = value
            
    
    def reset_to_initial_state(self)-> None:
        """
        Resets the battery to its initial state.
        """
        return True


    def __run_simulation(self, current:float, ambient_temp:float, time_duration: int, parameter_values, states_list : list) -> tuple[dict, list]:
        
        
        sim = pybamm.Simulation(self.model, parameter_values=parameter_values, )
        solution  = sim.solve([0, time_duration], starting_solution=states_list[-1])

        states_list.append(solution)
        # results = {
        #     "time": solution["Time [s]"].entries,
        #     "voltage": solution["Terminal voltage [V]"].entries,
        #     "current": solution["Current [A]"].entries,
        #     "power": solution["Power [W]"].entries,
        #     "state_of_power": solution["State of power"].entries,
        #     "stored_energy": solution["Stored energy [Wh]"].entries,
        #     "temperature": solution["X-averaged cell temperature [K]"].entries,
        #     "remained_capacity": solution["Remaining capacity [A.h]"].entries,
        #     "state_of_charge": solution["State of Charge [%]"].entries,
        #     "state_of_health": solution["State of Health [%]"].entries,
        #     "number_of_cycles": solution["Number of cycles"].entries
        # }
        return states_list
    
    
    def __update_params(self, solutions) -> None:
        """
        Updates the state of the battery based on the simulation results.
        """
        
        solution = solutions[-1]
        self.state_of_charge = solution["State of Charge [%]"].entries[-1]
        self.voltage = solution["Battery voltage [V]"].entries[-1]
        self.cell_voltage = solution["Voltage [V]"].entries[-1]
        self.cell_current = solution["Current [A]"].entries[-1]
        self.current = self.cell_current * self._attributes["cell_parallel_number [uint]"]
        self.cell_power = solution["Power [W]"].entries[-1]
        self.power = self.cell_power * self._attributes["total_number_of_cells [uint]"]
        self.temperature = self.cell_temperature = solution["Cell temperature [C]"].entries[-1]
        self.state_of_health = self.cell_state_of_health = self.__update_state_of_health(self, solution)
        self.state_of_charge = self.cell_state_of_charge = self.__update_state_of_charge(self, solution)
        self.cell_stored_energy = self.__update_stored_energy(self, solution)
        self.stored_energy = self.cell_stored_energy * self._attributes["total_number_of_cells [uint]"]
        self.cell_remained_capacity = self.__update_remained_capacity(self, solution)
        self.remained_capacity = self.cell_remained_capacity * self._attributes["total_number_of_cells [uint]"]
        self.state_of_power = self.cell_state_of_power = self.__update_state_of_power(self, solution)
 

    
    def report_state(self) -> dict:
        """
        Records the current state of the battery.
        
        Returns:
            dict: A dictionary of battery parameters with a timestamp.
        """
        return {
            "timestamp": datetime.now(),
            "state_of_charge": self.state_of_charge,
            "state_of_health": self.state_of_health,
            "voltage": self.voltage,
            "current": self.current,
            "power": self.power,
            "state_of_power": self.state_of_power,
            "stored_energy": self.stored_energy,
            "temperature": self.temperature,
            "remained_capacity": self.remained_capacity
    }
    
    
    def update_current(self, current:float) -> None:
        """
        Updates the current flowing into or out of the battery.
        
        This method modifies the `current` attribute in place and does not return a value.
        """
        self.current = current
    
        
    def __update_state_of_charge(self) -> None:
        
        
        return soc
              
    def __update_state_of_power(self) -> None:
        """
        Updates the state of power of the battery based on the power.
        
        This method modifies the `state_of_power` attribute in place and does not return a value.
        """
        self.state_of_power = self.power / self.power_max    
        
    
    def __update_remained_capacity(self):
        """
        Updates the total remained capacity of the battery based on the capacity and state of health.
        
        This method modifies the `remained_capacity` attribute in place and does not return a value.
        """
        self.remained_capacity  = self.nominal_capacity * (self.state_of_health/100) # Ah

        
    def __update_stored_energy(self):
        """
        Updates the available energy of the battery based on the total remained capacity, state of charge, and voltage.
        
        This method modifies the `stored_energy` attribute in place and does not return a value.
        """
        
        self.stored_energy = self.remained_capacity * (self.state_of_charge/100) * self.voltage # Wh   
    
 
    def __update_state_of_health(self, solution) -> float:
        """
        Calculate the State of Health (SOH) of a battery.

        Parameters:
        nominal_capacity (float): Nominal capacity of the battery (Ah).
        lam_negative (float): Loss of active material in the negative electrode (%).
        lam_positive (float): Loss of active material in the positive electrode (%).
        lli (float): Loss of lithium inventory (%).

        Returns:
        float: SOH value in percentage.
        """
        f_negative = 1 - solution["Loss of active material in negative electrode [%]"].entries[-1] / 100
        f_positive = 1 - solution["Loss of active material in positive electrode [%]"].entries[-1] / 100
        f_lli = 1 - solution["Loss of lithium inventory [%]"].entries[-1] / 100
        f_min = min(f_negative, f_positive, f_lli)
        current_capacity = self.__attributes["nominal_capacity [Ah]"] * f_min
        soh = (current_capacity / self.__attributes["nominal_capacity [Ah]"]) * 100
        return soh


    # def update_number_of_cycles(self):
    #     """
    #     Updates the number of cycles the battery has gone through based on the state of charge and the daily change in SOH.
        
    #     This method modifies the `number_of_cycles` attribute in place and does not return a value.
    #     """
        
    #     self.number_of_cycles += 1


    def __validate_operation(self):
        """
        Validates the dynamic parmateters range during operation against the specified constraints.
        
        Raises:
            ValueError: If any of the constraints are violated.
        """
        
        if not (self.state_of_charge_min <= self.state_of_charge <= self.state_of_charge_max):
            raise ValueError("State of Charge out of bounds")
        if not (self.voltage_min <= self.voltage <= self.voltage_max):
            raise ValueError("Voltage out of bounds")
        if not ( 0<= self.temperature <= 60): 
            raise ValueError("Overheating detected")
        if not (self.power <= self.power_max):
            raise ValueError("Power out of bounds")
        if not (abs(self.current) <= self.current_max):
            raise ValueError("Current out of bounds")
        if not ( 0 <= self.state_of_power <= 1):
            raise ValueError("State of Power out of bounds")
        if not (0 <= self.stored_energy <= self.nominal_capacity * self.voltage_max):
            raise(ValueError("Stored Energy out of bounds"))
        if not (0 <= self.remained_capacity <= self.nominal_capacity):
            raise(ValueError("Remained Capacity out of bounds"))
        if not (0 <= self.state_of_health <= 100):
            raise(ValueError("State of Health out of bounds"))
        if (self.state_of_health <= self.end_of_life):
            raise(ValueError("End of Life reached"))

     
    def simulate_and_update_state(self, current:float, ambient_temp:float, time_duration: int, previous_state: dict) -> tuple[bool, dict]:

        try:
            current_state  = self.__run_simulation(self, current, ambient_temp, time_duration, previous_state)
            self.__update_params(self, current_state)
            self.__validate_operation(self)
            return True, current_state
        except ValueError as e:
            print(f"Validation failed: {e}")
            return False, previous_state
        
                
    def __repr__(self):
        return f"""Energy Storage Model Specifications:
        - Cell Voltage: {self.cell_voltage} V
        - Cell Stored Energy: {self.cell_stored_energy} Wh
        - Cell Nominal Capacity: {self._attributes["nominal_cell_capacity [Ah]"]} Ah
        - Internal Resistance: {self._attributes["conctact_resistance [mΩ]"]} mΩ
        - Battery charge Efficiency: {self._attributes["charge_efficiency [%]"]} %
        - Battery discharge Efficiency: {self._attributes["discharge_efficiency [%]"]} %
        - Continuous Discharge Current: {self._attributes["discharge_current_max [A]"]} A
        - Continuous Charge Current: {self._attributes["charge_current_max [A]"]} A
        - End_of_life: {self._attributes["end_of_life_point [%]"]} %
        - state_of_charge: {self.state_of_charge} %
        - state_of_health: {self.state_of_health} %
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