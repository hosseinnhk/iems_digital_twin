# source/building_network/grid.py
# from .electrical_component import ElectricalComponent
from .print_theme import *

class Grid:
    
    def __init__(self, id, bus, max_power=10000.0, voltage=230.0, phase_type="single", 
                 technology="ac", status="on", active_power=0.0, reactive_power=0.0):
        """
        Initialize an external grid connection.
        
        Parameters:
        - id (str): Unique identifier.
        - bus (Bus): The bus this grid is connected to.
        - max_power (float): Maximum power capacity in watts (W).
        - voltage (float or tuple): Nominal voltage (e.g., 230V for single-phase, 
          (230, 400) for 3-phase line-to-neutral and line-to-line).
        - phase_type (str): "single" or "three" for AC; "single" for DC.
        - technology (str): "ac" or "dc".
        - active (bool): Whether the grid is operational.
        """
        # Set Grid-specific attributes before parent init
        self.max_power = float(max_power)
        self.voltage = voltage  # Grid enforces this voltage at the bus
        self.max_power = 0.0  # max power supplied (W)
        self.active_power = active_power  # active power supplied (W)
        self.reactive_power = reactive_power  # reactive power supplied (VAR)
        self.status = status
        self.bus = bus
        self.id = id
        self.phase_type = phase_type
        self.technology = technology

        # # Now call parent init, which triggers _validate_inputs()
        # super().__init__(id, bus, phase_type=phase_type, type="grid", technology=technology, 
        #                  voltage_rating=voltage, status=status)
        
        self._validate_inputs()

    def _validate_inputs(self):
        """Validate grid parameters."""
        if self.max_power < 0:
            raise ValueError(f"max_power must be non-negative, got {self.max_power}")
        if isinstance(self.voltage, tuple) and self.technology == "dc":
            raise ValueError("DC grid must have a single voltage, not a tuple")
        if isinstance(self.voltage, tuple) and self.phase_type != "three":
            raise ValueError("Tuple voltage is only valid for three-phase grids")

    def supply_power(self, required_power):
        if self.status == "off":
            return 0.0 if self.technology == "dc" else complex(0, 0)
        if self.max_power is None:  # Unlimited capacity
            self.active_power = required_power.real if self.technology == "ac" else required_power
            self.reactive_power = required_power.imag if self.technology == "ac" else 0.0
            return required_power
        if self.technology == "dc":
            if abs(required_power) > self.max_power:
                power = self.max_power if required_power > 0 else -self.max_power
            else:
                power = required_power
            self.active_power = power
            self.reactive_power = 0.0
            return power
        else:
            req_active = required_power.real
            req_reactive = required_power.imag
            total_apparent = (req_active**2 + req_reactive**2)**0.5
            if total_apparent > self.max_power:
                scale = self.max_power / total_apparent
                active = req_active * scale
                reactive = req_reactive * scale
            else:
                active = req_active
                reactive = req_reactive
            self.active_power = active
            self.reactive_power = reactive
            return complex(active, reactive)

    def connect_to_bus(self, bus):
        self.bus = bus
        # print(f"Initialized {self.id} to connect to bus {bus.id}")
        print_message_network(f"Initialized {self.id} to connect to bus {bus.id}")

    def enforce_voltage(self):
        """Set the bus voltage to the grid's nominal voltage."""
        if self.status == "on":
            self.bus.set_voltage(self.voltage)


    def get_power(self):
        """Return current power (positive = supplying, negative = absorbing)."""
        if self.status == "off":
            return 0.0 if self.technology == "dc" else complex(0, 0)
        if self.technology == "dc":
            return self.active_power
        return complex(self.active_power, self.reactive_power)

    def get_status(self):
        """Return grid status."""
        base_status = super().get_status()
        base_status.update({
            "max_power": self.max_power,
            "voltage": self.voltage
        })
        return base_status

        
    