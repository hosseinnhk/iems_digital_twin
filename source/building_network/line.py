# source/building_network/line.py
from .bus import Bus
from .electrical_component import ElectricalComponent

class Line:
    def __init__(self, id, bus_from, bus_to, length=1.0, resistance=0.01, reactance=0.0, 
                 phase_type="single", technology="ac"):
        """
        Initialize an electrical line connecting two buses.
        
        Parameters:
        - id (str): Unique identifier.
        - bus_from (Bus): Starting bus.
        - bus_to (Bus): Ending bus.
        - length (float): Line length in meters (default 1m).
        - resistance (float): Resistance in ohms per phase (default 0.01Ω).
        - reactance (float): Reactance in ohms per phase (AC only, default 0Ω).
        - phase_type (str): "single" or "three" for AC; "single" for DC.
        - technology (str): "ac" or "dc".
        """
        self.id = id
        self.bus_from = bus_from
        self.bus_to = bus_to
        self.length = float(length)
        self.resistance = float(resistance)
        self.reactance = float(reactance) if technology == "ac" else 0.0
        self.phase_type = phase_type.lower()
        self.technology = technology.lower()
        self._validate_inputs()

    def _validate_inputs(self):
        """Validate line parameters."""
        valid_technologies = {"ac", "dc"}
        valid_phase_types = {"single", "three"}
        
        if not isinstance(self.bus_from, Bus) or not isinstance(self.bus_to, Bus):
            raise ValueError("bus_from and bus_to must be Bus instances")
        if self.technology not in valid_technologies:
            raise ValueError(f"technology must be one of {valid_technologies}, got {self.technology}")
        if self.phase_type not in valid_phase_types:
            raise ValueError(f"phase_type must be one of {valid_phase_types}, got {self.phase_type}")
        if self.technology == "dc" and self.phase_type == "three":
            raise ValueError("DC lines cannot be three-phase")
        if self.technology == "dc" and self.reactance != 0:
            raise ValueError("DC lines cannot have reactance")
        if self.length <= 0:
            raise ValueError(f"Length must be positive, got {self.length}")
        if self.resistance < 0:
            raise ValueError(f"Resistance must be non-negative, got {self.resistance}")
        if self.reactance < 0:
            raise ValueError(f"Reactance must be non-negative, got {self.reactance}")
        if self.bus_from.technology != self.technology or self.bus_to.technology != self.technology:
            raise ValueError("Line technology must match both buses")
        if self.bus_from.phase_type != self.phase_type or self.bus_to.phase_type != self.phase_type:
            raise ValueError("Line phase_type must match both buses")

    def get_impedance(self):
        """Return the line impedance (R + jX for AC, R for DC)."""
        if self.technology == "dc":
            return self.resistance
        return complex(self.resistance, self.reactance)
    
    def connect_to_bus(self,bus, side=None):
        """Connect the line to the two buses."""
        self.bus = bus
        if side == "from":
            self.bus_from = bus
            # print(f"Connected line {self.id} to bus {bus.id} on the 'from' side")
        elif side == "to":
            self.bus_to = bus
            # print(f"Connected line {self.id} to bus {bus.id} on the 'to' side")
        else:
            raise ValueError("Line connection requires side='from' or 'to'")

    def calculate_power_loss(self, current):

        if self.technology == "dc":
            return (current ** 2) * self.resistance
        # For AC, assume current is complex or magnitude; loss is I^2 * Z
        if isinstance(current, complex):
            current_magnitude = abs(current)
        else:
            current_magnitude = current
        active_loss = (current_magnitude ** 2) * self.resistance
        reactive_loss = (current_magnitude ** 2) * self.reactance
        return complex(active_loss, reactive_loss)

    def get_status(self):
        return {
            "id": self.id,
            "bus_from": self.bus_from.id,
            "bus_to": self.bus_to.id,
            "length": self.length,
            "resistance": self.resistance,
            "reactance": self.reactance if self.technology == "ac" else None,
            "phase_type": self.phase_type,
            "technology": self.technology,
            "impedance": self.get_impedance()
        }