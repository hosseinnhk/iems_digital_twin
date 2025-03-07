# source/building_network/pv.py
from .electrical_component import ElectricalComponent

class PV(ElectricalComponent):
    def __init__(self, id, bus, max_power=5000.0, efficiency=0.18, area=10.0, 
                 phase_type="single", technology="dc", voltage_rating=None, status="on"):
        """
        Initialize a photovoltaic (PV) system.
        
        Parameters:
        - id (str): Unique identifier.
        - bus (Bus): The bus this PV is connected to.
        - max_power (float): Maximum power output in watts (W) under standard conditions.
        - efficiency (float): Conversion efficiency (0 to 1).
        - area (float): Panel area in square meters (m²).
        - phase_type (str): "single" or "three" for AC; "single" for DC.
        - technology (str): "dc" (typical) or "ac" (if inverter-integrated).
        - voltage_rating (float or tuple): Rated voltage (e.g., 48V for DC).
        - active (bool): Whether the PV is operational.
        """
        self.max_power = float(max_power)
        self.efficiency = float(efficiency)
        self.area = float(area)
        self.current_irradiance = 0.0  # W/m², set via generate_power        
        super().__init__(id, bus, phase_type=phase_type, type="generator", technology=technology, 
                         voltage_rating=voltage_rating, status=status)

        self._validate_inputs()

    def _validate_inputs(self):
        """Validate PV parameters."""
        if self.max_power < 0:
            raise ValueError(f"max_power must be non-negative, got {self.max_power}")
        if not 0 < self.efficiency <= 1:
            raise ValueError(f"efficiency must be between 0 and 1, got {self.efficiency}")
        if self.area <= 0:
            raise ValueError(f"area must be positive, got {self.area}")

    def generate_power(self, irradiance):
        """
        Generate power based on solar irradiance.
        
        Parameters:
        - irradiance (float): Solar irradiance in W/m².
        Returns: Actual power generated in watts.
        """
        if self.status == "off":
            return 0.0
        if irradiance < 0:
            raise ValueError(f"irradiance must be non-negative, got {irradiance}")

        self.current_irradiance = float(irradiance)
        potential_power = self.area * self.current_irradiance * self.efficiency
        actual_power = min(potential_power, self.max_power)
        self.active_power = actual_power
        self.reactive_power = 0.0  # PV typically doesn't supply reactive power
        return actual_power

    def get_power(self):
        """Return current power generated."""
        if self.status == "off":
            return 0.0 if self.technology == "dc" else complex(0, 0)
        if self.technology == "dc":
            return self.active_power
        return complex(self.active_power, self.reactive_power)

    def get_status(self):
        """Return PV status."""
        base_status = super().get_status()
        base_status.update({
            "max_power": self.max_power,
            "efficiency": self.efficiency,
            "area": self.area,
            "current_irradiance": self.current_irradiance
        })
        return base_status