from scipy.integrate import quad
import numpy as np
from datetime import datetime
from typing import Any
import pybamm
import logging

class EnergyStorageModel:
    
    def __init__(self):
   
        super().__setattr__('_attributes', {})
        
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
        
        self.validation_rules = {
            "time_resolution [s]": lambda v: v > 0,  # Time resolution must be positive
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
        }

    def get_cell_state_of_charge(self):
        return self.cell_state_of_charge
    
    def set_cell_state_of_charge(self, value):
        if 0 <= value <= 100:
            self.cell_state_of_charge = value
        else:
            raise ValueError("State of Charge must be between 0 and 100")

    # Getter and Setter for cell_state_of_health
    def get_cell_state_of_health(self):
        return self.cell_state_of_health
    
    def set_cell_state_of_health(self, value):
        if 0 <= value <= 100:
            self.cell_state_of_health = value
        else:
            raise ValueError("State of Health must be between 0 and 100")

    # Getter and Setter for cell_voltage
    def get_cell_voltage(self):
        return self.cell_voltage
    
    def set_cell_voltage(self, value):
        if value >= 0:
            self.cell_voltage = value
        else:
            raise ValueError("Voltage must be a positive number")

    # Getter and Setter for cell_current
    def get_cell_current(self):
        return self.cell_current
    
    def set_cell_current(self, value):
        if value >= 0:
            self.cell_current = value
        else:
            raise ValueError("Current must be a positive number")

    # Getter and Setter for cell_power
    def get_cell_power(self):
        return self.cell_power
    
    def set_cell_power(self, value):
        if value >= 0:
            self.cell_power = value
        else:
            raise ValueError("Power must be a positive number")

    # Getter and Setter for cell_state_of_power
    def get_cell_state_of_power(self):
        return self.cell_state_of_power
    
    def set_cell_state_of_power(self, value):
        if 0 <= value <= 100:
            self.cell_state_of_power = value
        else:
            raise ValueError("State of Power must be between 0 and 100")

    # Getter and Setter for cell_stored_energy
    def get_cell_stored_energy(self):
        return self.cell_stored_energy
    
    def set_cell_stored_energy(self, value):
        if value >= 0:
            self.cell_stored_energy = value
        else:
            raise ValueError("Stored Energy must be a positive number")

    # Getter and Setter for cell_temperature
    def get_cell_temperature(self):
        return self.cell_temperature
    
    def set_cell_temperature(self, value):
        if -273.15 <= value:
            self.cell_temperature = value
        else:
            raise ValueError("Temperature cannot be below absolute zero")

    # Getter and Setter for cell_remained_capacity
    def get_cell_remained_capacity(self):
        return self.cell_remained_capacity
    
    def set_cell_remained_capacity(self, value):
        if value >= 0:
            self.cell_remained_capacity = value
        else:
            raise ValueError("Remained Capacity must be a positive number")

    # Similarly, you can create getters and setters for other dynamic variables, e.g., state_of_charge, voltage, power, etc.

    # Getter and Setter for _attributes (for constants)
    def get_attribute(self, key):
        if key in self._attributes:
            return self._attributes[key]
        else:
            raise KeyError(f"Attribute {key} not found")
    
    def set_attribute(self, key, value):
        if key in self._attributes:
            # Apply validation rule for the specific attribute
            if key in self.validation_rules and self.validation_rules[key](value):
                self._attributes[key] = value
            else:
                raise ValueError(f"Invalid value for {key}")
        else:
            raise KeyError(f"Attribute {key} not found")        
           
    # def __getattr__(self, name: str) -> Any:
    #     """Get the value of an attribute."""
    #     # First, check if the attribute is in _attributes
    #     if name in self._attributes:
    #         return self._attributes[name]
    #     # Then, check if it's a regular instance attribute (directly assigned in __init__)
    #     try:
    #         return object.__getattribute__(self, name)  # Avoid recursion, get directly
    #     except AttributeError:
    #         raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


    # def __setattr__(self, name: str, value: Any)-> None:
    #     """
    #     Set the value of an attribute.
        
    #     Args:
    #         name (str): The name of the attribute.
    #         value (Any): The value of the attribute.
    #     """
    #     if name in self.validation_rules:
    #         if not self.validation_rules[name](value):
    #             raise ValueError(f"Invalid value for {name}: {value}")
    #         self._attributes[name] = value
    #     elif name.startswith('cell_') or name.startswith('state_') or name.startswith('voltage') or name.startswith('temperature'):
    #         # Handle dynamic variables that are not stored in _attributes
    #         super().__setattr__(name, value)
    #     else:
    #         super().__setattr__(name, value)
    
            
    def __validate_parameter(self, key, value):
        """
        Validates a single parameter using the validation rules.
        Logs a warning if the parameter is invalid.
        """
        if key in self.validation_rules:
            is_valid = self.validation_rules[key](value)
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
        self.model = pybamm.lithium_ion(parameters['cell_model'])
        parameters_value = pybamm.ParameterValues(parameters['cell_chemistry'])
        
        excluded_parameters = ["cell_series_number [uint]", "cell_parallel_number [uint]", "voltage_max [v]", "voltage_min [v]", "total_number_of_cells [uint]", 
            "voltage_max [v]", "cell_voltage_max [v]", "voltage_min [v]", "cell_voltage_min [v]", "nominal_cell_capacity [Ah]", "cell_power_max [w]", "cell_discharge_current_max [A]",
            "cell_charge_current_max [A]", "c_rate_charge_max", "c_rate_discharge_max","state_of_health_init [%]","end_of_life_point [%]", "conctact_resistance [mΩ]", "temperature_max [°C]"]
        
        for key in self.validation_rules:
            if key not in parameters and key not in excluded_parameters:
                raise KeyError(f"Missing required parameter: {key}")
            
            value = parameters[key]
            if not (self.__validate_parameter(key, value)):
                raise ValueError(f"Invalid value for {key}: {value}")
        logging.info("All parameters for initialization are valid")
        
        self["time_resolution [s]"] = parameters["time_resolution [s]"]
        self["state_of_charge_init [%]"] = parameters["state_of_charge_init [%]"]
        self["state_of_health_init [%]"] = parameters["state_of_health_init [%]"]
        
        self.cell_state_of_charge = self.state_of_charge = self.get("state_of_charge_init [%]", 50.0)      
        self.cell_state_of_health = self.state_of_health = self.get("state_of_health_init [%]", 100.0)
        
        self["nominal_capacity [Ah]"] = parameters["nominal_capacity [Ah]"] 
        self["nominal_voltage [v]"] = parameters["nominal_voltage [v]"]
        self["nominal_cell_voltage [V]"]= parameters["nominal_cell_voltage [V]"]

        
        self["nominal_cell_capacity [Ah]"] = parameters_value["Nominal cell capacity [A.h]"]
        self["cell_voltage_max [v]"] = parameters_value["Upper voltage cut-off [V]"]
        self["cell_voltage_min [v]"] = parameters_value["Lower voltage cut-off [V]"]
        
        self.cell_temperature = parameters["ambient_temperature [°C]"]
        self.temperature = self.cell_temperature

        self["cell_series_number [uint]"] = np.ceil(self["nominal_voltage [v]"]/ self["nominal_cell_voltage [V]"])
        self["cell_parallel_number [uint]"] = np.ceil(self["nominal_capacity [Ah]"] / self["nominal_cell_capacity [Ah]"])
        

        self["nominal_capacity [Ah]"] = self["nominal_cell_capacity [Ah]"] * self["cell_parallel_number [uint]"] 
        self["nominal_voltage [V]"] = self["nominal_cell_voltage [V]"] * self["cell_series_number [uint]"]
        
        self["voltage_max [v]"] = self["cell_voltage_max [v]"] * self["cell_series_number [uint]"]
        self["voltage_min [v]"] = self["cell_voltage_min [v]"] * self["cell_series_number [uint]"]
        

        parameters_value["Number of cells connected in series to make a battery"] = self["cell_series_number [uint]"]
        parameters_value["Number of electrodes connected in parallel to make a cell"] = self["cell_parallel_number [uint]"] 
        self["total_number_of_cells [uint]"] = self["cell_series_number [uint]"] * self["cell_parallel_number [uint]"]
        
        self.current = parameters["current [A]"]
        self.cell_current  = self.current / self["cell_parallel_number [uint]"] 
        
        
        parameters_value["Ambient temperature [K]"] = parameters["ambient_temperature [°C]"] + 273.15
        parameters_value["Initial temperature [K]"] = parameters["ambient_temperature [°C]"] + 273.15
        parameters_value['Current function [A]' ] = self.cell_current
        
        sim = pybamm.Simulation(self.model, parameter_values=parameters_value)
        sim.solve([0, 1])
        
        self.cell_voltage = sim.solution["Terminal voltage [V]"](1)
        self.voltage = self.cell_voltage * self.cell_series_number
        
      
        self.cell_power = self.cell_current * self.cell_voltage # Power, in Watts (W)
        self.power = self.cell_power * self["total_number_of_cells [uint]"] # Power, in Watts (W)
        
        self["power_max [w]"] = parameters["power_max [w]"]
        self["cell_power_max [w]"] = self["power_max [w]"] / (self["total_number_of_cells [uint]"]) # Power, in Watts (W)
        
        
        self.cell_state_of_power = self.cell_power / self["cell_power_max [w]"]  # Power/Power_max in percentage (%)
        self.state_of_power = self.cell_state_of_power
        
        self.cell_remained_capacity = self["nominal_cell_capacity [Ah]"] * (self["state_of_health_init [%]"] / 100)  # Ah
        self.remained_capacity = self.cell_remained_capacity * self["total_number_of_cells [uint]"]  # Ah
        
        self.cell_stored_energy = self.cell_remained_capacity * self.cell_voltage * (self["state_of_charge_init [%]"] / 100)  # Wh
        self.stored_energy = self.cell_stored_energy * self["total_number_of_cells [uint]"]  # Wh
        
        self["discharge_current_max [A]"] = parameters_value["Maximum discharge current [A]"]
        self["cell_discharge_current_max [A]"] = self["discharge_current_max [A]"] / self.cell_parallel_number
        self["charge_current_max [A]"] = parameters_value["Maximum charge current [A]"]
        self["cell_charge_current_max [A]"] = self["charge_current_max [A]"] / self.cell_parallel_number
        
        self["end_of_life_point [%]"] = parameters["end_of_life_point [%]"]
        self["state_of_charge_min [%]"] = parameters["state_of_charge_min [%]"]
        self["state_of_charge_max [%]"] = parameters["state_of_charge_max [%]"]
        self["charge_efficiency [%]"] = parameters["charge_efficiency [%]"]
        self["discharge_efficiency [%]"] = parameters["discharge_efficiency [%]"]
        self["temperature_max [°C]"] = parameters["temperature_max [°C]"]
        
        self["conctact_resistance [mΩ]"] = parameters_value["Contact resistance [Ohm]"] * 1000
        self["c_rate_charge_max"] = parameters["c_rate_charge_max"]
        self["c_rate_discharge_max"] = parameters["c_rate_discharge_max"]
        
        
        for key in self.validation_rules:
        
            value = parameters[key]
            if not (self.__validate_parameter(key, value)):
                raise ValueError(f"Invalid value for {key}: {value}")
        logging.info("All parameters are intialized and validated")
        
        return self.model, parameters_value
    
     
    def _update_constants_batch(self, new_constants: dict)-> None:
        """
        Updates the constants of the battery model.
        
        Args:
            new_constants (dict): A dictionary of new constants.
            
        Raises:
            AttributeError: If the constant is not valid.
            ValueError: If the value of the constant is invalid
        """
        for key, value in new_constants.items():
            if key not in self.validation_rules:
                raise AttributeError(f"{key} is not a valid constant in EnergyStorageModel")
            if not self.validation_rules[key](value):
                raise ValueError(f"Invalid value for {key}: {value}")
        
        for key, value in new_constants.items():
            self._attributes[key] = value
            
    
    def reset_to_initial_state(self)-> None:
        """
        Resets the battery to its initial state.
        """
        self.state_of_charge = self.state_of_charge_init
        self.state_of_health = self.state_of_health_init
        self.nominal_capacity = self.cell_capacity * self.cell_series_number * self.cell_parallel_number * self.state_of_health_init # Ah
        self.stored_energy = self.nominal_capacity * self.voltage * (self.state_of_charge_init / 100)  # Wh
        self.temperature = self.cell_temperature
    
    
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
    
        
    def update_state_of_charge(self) -> None:
        """
        Updates the state of charge (SOC) of the battery based on the current, 
        time resolution, and total remaining capacity.
        
        This method modifies the `state_of_charge` attribute in place and does not return a value.
        """
        # Calculate the charge transferred during the time interval (Ah)
        charge_transferred = (self.time_resolution * self.current) / 3600
        
        # Update the state of charge
        self.state_of_charge += charge_transferred / self.remained_capacity
        
        # Clamp the state of charge within the allowed range
        self.state_of_charge = max(
            self.state_of_charge_min, 
            min(self.state_of_charge, self.state_of_charge_max)
        )
    
    
    def update_voltage(self) -> None:
        """
        Updates the voltage of the battery based on the current flowing through it.
        
        This method modifies the `voltage` attribute in place and does not return a value.
        """
        
        internal_voltage_drop = self.current * (self.internal_resistance / 1000)
        self.voltage = ((self.state_of_charge + 735) / 250)*100 - internal_voltage_drop
        
        
    def update_power(self) -> None:
        """
        Updates the power of the battery based on the voltage and current.
        
        This method modifies the `power` attribute in place and does not return a value.
        """
        self.power = self.voltage * self.current  
        
        
    def update_state_of_power(self) -> None:
        """
        Updates the state of power of the battery based on the power.
        
        This method modifies the `state_of_power` attribute in place and does not return a value.
        """
        self.state_of_power = self.power / self.power_max    
        
    
    def update_remained_capacity(self):
        """
        Updates the total remained capacity of the battery based on the capacity and state of health.
        
        This method modifies the `remained_capacity` attribute in place and does not return a value.
        """
        self.remained_capacity  = self.nominal_capacity * (self.state_of_health/100) # Ah

        
    def update_stored_energy(self):
        """
        Updates the available energy of the battery based on the total remained capacity, state of charge, and voltage.
        
        This method modifies the `stored_energy` attribute in place and does not return a value.
        """
        
        self.stored_energy = self.remained_capacity * (self.state_of_charge/100) * self.voltage # Wh   
    
    
    def update_temp(self, ambient_temp:float) -> None:
        """
        Updates the temperature of the battery based on the current, internal resistance, and ambient temperature.
        
        This method modifies the `temperature` attribute in place and does not return a value.
        """
        heat_generated = (self.current ** 2) * (self.internal_resistance / 1000)
        self.temperature += (heat_generated / (self.cell_series_number * self.cell_parallel_number)) * self.time_resolution - 0.1 * (self.temperature - ambient_temp)
    
    
    def update_state_of_health(self):
        """
        Updates the state of health (SOH) of the battery based on the state of charge and the daily change in SOH.
        
        This method modifies the `state_of_health` attribute in place and does not return a value.
        """
        
        self.state_of_health -= self.__state_of_health_daily_change(self.state_of_charge, self["nominal_cell_capacity [Ah]"])


    def update_number_of_cycles(self):
        """
        Updates the number of cycles the battery has gone through based on the state of charge and the daily change in SOH.
        
        This method modifies the `number_of_cycles` attribute in place and does not return a value.
        """
        
        self.number_of_cycles += 1


    def validate_operation(self):
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

     
    def update_ess_state(self, current:float, ambient_temp:float) -> bool:
        """
        Updates the state of the battery based on the current and ambient temperature.
        
        Args:
            current (float): The current flowing into or out of the battery, in Amperes (A).
            ambient_temp (float): The ambient temperature, in Celsius (°C).
            
        Returns:
            bool: True if the operation is successful.
        """
        try:
            self.update_current(current)
            self.update_state_of_charge()
            self.update_voltage()
            self.update_power()
            self.update_state_of_power()
            self.update_remained_capacity()
            self.update_stored_energy()
            self.update_temp(ambient_temp)
            self.update_state_of_health()
            self.validate_operation()
            return True
        except ValueError as e:
            print(f"Validation failed: {e}")
            return False
        
    """===============`Private Methods`================"""  
    def __state_of_charge_avg(self):
            
            delta_Qt =  0.0       # Calculate the charge transferred during the time interval (Ah)
            charge_transferred = (self.time_resolution * self.current) / 3600
            state_of_charge_avg, _ = quad(lambda Q: self.__state_of_charge(Q, self.remained_capacity), Qt_1, Qt)
            state_of_charge_avg = state_of_charge_avg / delta_Qt
            return state_of_charge_avg


    def __state_of_charge_dev(self, Qt_1, Qt, Qmax):
        
        delta_Qt = Qt - Qt_1
        state_of_charge_avg = self.__state_of_charge_avg(Qt_1, Qt, Qmax)
        integral_result, _ = quad(lambda Q: (self._state_of_charge(Q, Qmax) - state_of_charge_avg) ** 2, Qt_1, Qt)
        state_of_charge_dev = np.sqrt(abs((3 / delta_Qt) * integral_result))
        return state_of_charge_dev
    
    
    def __Fi(self, state_of_charge_dev, state_of_charge_avg):
        
        F = (self.k_s1 * state_of_charge_dev * np.exp(self.k_s2 * state_of_charge_avg) + self.k_s3 * np.exp(self.k_s4 * state_of_charge_dev))
        return F


    def __c_cycle(F, Q, Ea, R, T, T_ref):

        c_cycle = sum(F[i] * abs(Q[i]-Q[i-1]) * np.exp(( -Ea / R ) * (1 / T - 1 / T_ref)) for i in range(len(F)))
        return c_cycle


    def __c_cal_1h(state_of_charge_1h_avg):

        
        return  (6.6148 * state_of_charge_1h_avg + 4.6404) * 10**-6


    def __c_cal(c_cal_1h_list):

        c_cal = sum(c_cal_1h_list)
        return c_cal


    def __c_cycle_day(c_cycle_1h_list):

        c_cycle_day= sum(c_cycle_1h_list)
        return c_cycle_day


    def __state_of_health(c_cal, c_cycel, c_nm):
        c_fd = c_cal + 100 * c_cycel/c_nm
        # state_of_health = 100 - c_fd
        return c_fd

    
    def __state_of_health_daily_change(self, Qt: list, Qmax: float):
        
        c_cal_day = []
        c_cycle_day = []
        
        for i in range(int(len(Qt)/24)): # 0-23
            Fi = []
            Qi = []
            state_of_charge_avg_1h = 0.0
            
            # first we calculate soh changes for each hour: 
            for j in range(12): # 0-11
                if i*12+j-1 > 0 : 
                    state_of_charge_avg = self.__state_of_charge_avg(self, Qt[i*12+j-1], Qt[i*12+j], Qmax)
                    state_of_charge_dev = self.__state_of_charge_dev(self, Qt[i*12+j-1], Qt[i*12+j], Qmax)
                    Fi.append(self.__Fi(self, state_of_charge_avg, state_of_charge_dev))
                    Qi.append(Qt[i*12+j])
                    state_of_charge_avg_1h += state_of_charge_avg 
                    
            c_cycle_1h  = f_c_cycle(Fi, Qi, ess.E_a, ess.R, ess.T_i, ess.T_ref)
            c_cal_1h = f_c_cal_1h(state_of_charge_avg_1h/12)
            c_cal_day.append(c_cal_1h)
            c_cycle_day.append(c_cycle_1h)
            
        c_cal = f_c_cal(c_cal_day)
        c_cycle = f_c_cycle_day(c_cycle_day)
        delta_state_of_health = f_state_of_health(c_cal, c_cycle, Qmax)       
        if delta_state_of_health< 0: 
            delta_state_of_health = 0
        return delta_state_of_health

          
    def __repr__(self):
        return f"""Energy Storage Model Specifications:
        - Cell Voltage: {self.cell_voltage} V
        - Cell Stored Energy: {self.cell_stored_energy} Wh
        - Cell Nominal Capacity: {self["nominal_cell_capacity [Ah]"]} Ah
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
        - Voltage Min: {self.voltage_min} V
        - Capacity : {self.nominal_capacity} Wh
        - state_of_charge inti: {self.state_of_charge_init} % 
        - state_of_health init: {self.state_of_health_init} %
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