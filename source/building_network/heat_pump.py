# source/building_network/heat_pump.py
from .electrical_component import ElectricalComponent

class HeatPump(ElectricalComponent):
    def __init__(self, id, bus, rated_power=2000.0, cop=3.0, mode="heating", 
                 phase_type="single", technology="ac", voltage_rating=None, status="on"):
        """
        Initialize a heat pump for heating or cooling.
        
        Parameters:
        - id (str): Unique identifier.
        - bus (Bus): The bus this heat pump is connected to.
        - rated_power (float): Nominal electrical power consumption in watts (W).
        - cop (float): Coefficient of Performance (thermal output / electrical input).
        - mode (str): "heating" or "cooling" operation mode.
        - phase_type (str): "single" or "three" for AC; "single" for DC.
        - technology (str): "ac" (typical) or "dc".
        - voltage_rating (float or tuple): Rated voltage (e.g., 230V for AC).
        - active (bool): Whether the heat pump is operational.
        """
        self.rated_power = float(rated_power)
        self.cop = float(cop)
        self.mode = mode.lower()
        super().__init__(id, bus, phase_type=phase_type, type="heat_pump", technology=technology, 
                         voltage_rating=voltage_rating, status=status)

        self._validate_inputs()

    def _validate_inputs(self):
        """Validate heat pump parameters."""
        if self.rated_power < 0:
            raise ValueError(f"rated_power must be non-negative, got {self.rated_power}")
        if self.cop <= 0:
            raise ValueError(f"cop must be positive, got {self.cop}")
        if self.mode not in {"heating", "cooling"}:
            raise ValueError(f"mode must be 'heating' or 'cooling', got {self.mode}")

    def set_operating_condition(self, power_fraction=1.0):
        """
        Set the operating condition of the heat pump.
        
        Parameters:
        - power_fraction (float): Fraction of rated power (0 to 1).
        Returns: Thermal output in watts.
        """
        if self.status == "off":
            return 0.0
        if not 0 <= power_fraction <= 1:
            raise ValueError(f"power_fraction must be between 0 and 1, got {power_fraction}")

        # Electrical power consumed
        self.active_power = self.rated_power * power_fraction
        if self.technology == "ac" and self.reactive_power == 0.0:
            self.reactive_power = self.active_power * 0.2  # Assume PF=0.98, adjust as needed
        
        # Thermal power output (positive for heating, negative for cooling)
        thermal_output = self.active_power * self.cop
        if self.mode == "cooling":
            thermal_output = -thermal_output
        return thermal_output

    def get_power(self):
        """Return current electrical power consumed."""
        if self.status == "off":
            return 0.0 if self.technology == "dc" else complex(0, 0)
        if self.technology == "dc":
            return self.active_power
        return complex(self.active_power, self.reactive_power)

    def get_thermal_output(self):
        """Return current thermal power output (positive for heating, negative for cooling)."""
        if self.status == "off":
            return 0.0
        thermal_output = self.active_power * self.cop
        return thermal_output if self.mode == "heating" else -thermal_output

    def set_mode(self, mode):
        """Set the operating mode."""
        self.mode = mode.lower()
        self._validate_inputs()

    def get_status(self):
        """Return heat pump status."""
        base_status = super().get_status()
        base_status.update({
            "rated_power": self.rated_power,
            "cop": self.cop,
            "mode": self.mode,
            "thermal_output": self.get_thermal_output()
        })
        return base_status