# source/building_network/energy_storage.py
from .electrical_component import ElectricalComponent

class EnergyStorage(ElectricalComponent):
    def __init__(self, id, bus, capacity, initial_soc=0.5, max_charge_power=1000.0, 
                 max_discharge_power=1000.0, efficiency=0.95, phase_type="single", 
                 technology="dc", voltage_rating=None, status="on"):
        """
        Initialize an energy storage component (e.g., battery).
        
        Parameters:
        - id (str): Unique identifier.
        - bus (Bus): The bus this storage is connected to.
        - capacity (float): Total energy capacity in watt-hours (Wh).
        - initial_soc (float): Initial state of charge (0 to 1).
        - max_charge_power (float): Maximum charging power in watts (W).
        - max_discharge_power (float): Maximum discharging power in watts (W).
        - efficiency (float): Round-trip efficiency (0 to 1).
        - phase_type (str): "single" or "three" for AC; "single" for DC.
        - technology (str): "ac" or "dc".
        - voltage_rating (float or tuple): Rated voltage (e.g., 48V for DC, 230V for AC).
        - active (bool): Whether the storage is operational.
        """
        self.capacity = float(capacity)
        self.soc = float(initial_soc)  # State of Charge (0 to 1)
        self.max_charge_power = float(max_charge_power)
        self.max_discharge_power = float(max_discharge_power)
        self.efficiency = float(efficiency)
        super().__init__(id, bus, phase_type=phase_type, type="storage", technology=technology, 
                         voltage_rating=voltage_rating, status=status)

        self._validate_inputs()

    def _validate_inputs(self):
        """Validate energy storage parameters."""
        if not 0 <= self.soc <= 1:
            raise ValueError(f"SoC must be between 0 and 1, got {self.soc}")
        if self.capacity <= 0:
            raise ValueError(f"Capacity must be positive, got {self.capacity}")
        if self.max_charge_power < 0 or self.max_discharge_power < 0:
            raise ValueError("Charge and discharge powers must be non-negative")
        if not 0 < self.efficiency <= 1:
            raise ValueError(f"Efficiency must be between 0 and 1, got {self.efficiency}")

    def charge(self, power, time_step=1.0):
        """
        Charge the storage with given power for a time step.
        
        Parameters:
        - power (float): Charging power in watts (positive).
        - time_step (float): Time duration in hours (default 1 hour).
        Returns: Actual power absorbed (considering limits).
        """
        if self.status =="off":
            return 0.0
        if power < 0:
            raise ValueError("Charging power must be positive")

        # Limit power to max_charge_power
        effective_power = min(power, self.max_charge_power)
        energy_in = effective_power * time_step * self.efficiency  # Wh
        available_capacity = self.capacity * (1 - self.soc)
        
        if energy_in > available_capacity:
            energy_in = available_capacity
            effective_power = energy_in / (time_step * self.efficiency)
        
        self.soc += energy_in / self.capacity
        self.active_power = -effective_power  # Negative: power into storage
        self.reactive_power = 0.0 if self.technology == "dc" else self.reactive_power
        return effective_power

    def discharge(self, power, time_step=1.0):
        """
        Discharge the storage with given power for a time step.
        
        Parameters:
        - power (float): Discharging power in watts (positive).
        - time_step (float): Time duration in hours (default 1 hour).
        Returns: Actual power supplied (considering limits).
        """
        if self.status =="off":
            return 0.0
        if power < 0:
            raise ValueError("Discharging power must be positive")

        # Limit power to max_discharge_power
        effective_power = min(power, self.max_discharge_power)
        energy_out = effective_power * time_step / self.efficiency  # Wh
        available_energy = self.capacity * self.soc
        
        if energy_out > available_energy:
            energy_out = available_energy
            effective_power = energy_out * self.efficiency / time_step
        
        self.soc -= energy_out / self.capacity
        self.active_power = effective_power  # Positive: power out of storage
        self.reactive_power = 0.0 if self.technology == "dc" else self.reactive_power
        return effective_power

    def get_power(self):
        """Return current power (negative for charging, positive for discharging)."""
        if self.status =="off":
            return 0.0 if self.technology == "dc" else complex(0, 0)
        if self.technology == "dc":
            return self.active_power
        return complex(self.active_power, self.reactive_power)

    def set_reactive_power(self, reactive_power):
        """Set reactive power (AC only)."""
        if self.technology == "dc":
            raise ValueError("DC storage cannot have reactive power")
        self.reactive_power = float(reactive_power)

    def get_status(self):
        """Return storage status."""
        base_status = super().get_status()
        base_status.update({
            "capacity": self.capacity,
            "soc": self.soc,
            "max_charge_power": self.max_charge_power,
            "max_discharge_power": self.max_discharge_power,
            "efficiency": self.efficiency
        })
        return base_status