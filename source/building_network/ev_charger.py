# source/building_network/ev_charger.py
from .electrical_component import ElectricalComponent

class EVCharger(ElectricalComponent):
    def __init__(self, id, bus, max_charge_power=7000.0, max_discharge_power=7000.0, 
                 efficiency=0.95, ev_capacity=40000.0, initial_soc=0.5, 
                 phase_type="single", technology="ac", voltage_rating=None, active=True):
        """
        Initialize an EV charger with bidirectional (V2B/V2G) capability.
        
        Parameters:
        - id (str): Unique identifier.
        - bus (Bus): The bus this charger is connected to.
        - max_charge_power (float): Max charging power to EV in watts (W).
        - max_discharge_power (float): Max discharging power from EV in watts (W).
        - efficiency (float): Charger efficiency (0 to 1).
        - ev_capacity (float): EV battery capacity in watt-hours (Wh).
        - initial_soc (float): Initial state of charge of EV battery (0 to 1).
        - phase_type (str): "single" or "three" for AC; "single" for DC.
        - technology (str): "ac" (common) or "dc" (direct to EV battery).
        - voltage_rating (float or tuple): Rated voltage (e.g., 230V for AC).
        - active (bool): Whether the charger is operational.
        """
        self.max_charge_power = float(max_charge_power)
        self.max_discharge_power = float(max_discharge_power)
        self.efficiency = float(efficiency)
        self.ev_capacity = float(ev_capacity)
        self.soc = float(initial_soc)
        self.state = "idle"  # "idle", "charging", "discharging"
        super().__init__(id, bus, phase_type=phase_type, type="ev_charger", technology=technology, 
                         voltage_rating=voltage_rating, active=active)

        self._validate_inputs()

    def _validate_inputs(self):
        """Validate EV charger parameters."""
        if self.max_charge_power < 0 or self.max_discharge_power < 0:
            raise ValueError("Max charge/discharge powers must be non-negative")
        if not 0 < self.efficiency <= 1:
            raise ValueError(f"efficiency must be between 0 and 1, got {self.efficiency}")
        if self.ev_capacity <= 0:
            raise ValueError(f"ev_capacity must be positive, got {self.ev_capacity}")
        if not 0 <= self.soc <= 1:
            raise ValueError(f"soc must be between 0 and 1, got {self.soc}")

    def charge(self, power, time_step=1.0):
        """
        Charge the EV battery.
        
        Parameters:
        - power (float): Requested charging power in watts (positive).
        - time_step (float): Duration in hours (default 1 hour).
        Returns: Actual power consumed from the bus.
        """
        if not self.active:
            return 0.0
        if power < 0:
            raise ValueError("Charging power must be positive")
        
        self.state = "charging"
        effective_power = min(power, self.max_charge_power)
        energy_in = effective_power * time_step * self.efficiency  # Wh to EV
        available_capacity = self.ev_capacity * (1 - self.soc)
        
        if energy_in > available_capacity:
            energy_in = available_capacity
            effective_power = energy_in / (time_step * self.efficiency)
        
        self.soc += energy_in / self.ev_capacity
        self.active_power = effective_power  # Positive: power consumed from bus
        self.reactive_power = effective_power * 0.2 if self.technology == "ac" else 0.0  # Assume PF=0.98
        return effective_power

    def discharge(self, power, time_step=1.0):
        """
        Discharge the EV battery (V2B/V2G).
        
        Parameters:
        - power (float): Requested discharging power in watts (positive).
        - time_step (float): Duration in hours (default 1 hour).
        Returns: Actual power supplied to the bus.
        """
        if not self.active:
            return 0.0
        if power < 0:
            raise ValueError("Discharging power must be positive")
        
        self.state = "discharging"
        effective_power = min(power, self.max_discharge_power)
        energy_out = effective_power * time_step / self.efficiency  # Wh from EV
        available_energy = self.ev_capacity * self.soc
        
        if energy_out > available_energy:
            energy_out = available_energy
            effective_power = energy_out * self.efficiency / time_step
        
        self.soc -= energy_out / self.ev_capacity
        self.active_power = -effective_power  # Negative: power supplied to bus
        self.reactive_power = 0.0  # Assume no reactive power in discharge (adjustable)
        return effective_power

    def set_idle(self):
        """Set charger to idle state."""
        self.state = "idle"
        self.active_power = 0.0
        self.reactive_power = 0.0

    def get_power(self):
        """Return current power (positive = charging, negative = discharging)."""
        if not self.active:
            return 0.0 if self.technology == "dc" else complex(0, 0)
        if self.technology == "dc":
            return self.active_power
        return complex(self.active_power, self.reactive_power)

    def get_status(self):
        """Return EV charger status."""
        base_status = super().get_status()
        base_status.update({
            "max_charge_power": self.max_charge_power,
            "max_discharge_power": self.max_discharge_power,
            "efficiency": self.efficiency,
            "ev_capacity": self.ev_capacity,
            "soc": self.soc,
            "state": self.state
        })
        return base_status