# source/building_network/inverter.py
from .electrical_component import ElectricalComponent
# from .print_theme import *

class Inverter(ElectricalComponent):
    def __init__(self, id, bus_input, bus_output, input_technology="dc", output_technology="ac", 
                 efficiency=0.95, max_power=10000.0, status="on"):
        """
        Initialize a generic inverter connecting two buses with configurable technologies.
        
        Parameters:
        - id (str): Unique identifier.
        - bus_input (Bus): Input-side bus (e.g., DC from PV or AC from grid).
        - bus_output (Bus): Output-side bus (e.g., AC to load or DC to battery).
        - input_technology (str): "dc" or "ac" for input side.
        - output_technology (str): "dc" or "ac" for output side.
        - efficiency (float): Power conversion efficiency (0 to 1).
        - max_power (float): Maximum power throughput in watts.
        - active (bool): Whether the inverter is operational.
        """
        # Initialize base class with input bus as the primary bus
        super().__init__(id, bus_input, phase_type="single", type="inverter", technology=input_technology, status=status)
        self.bus_input = bus_input
        self.bus_output = bus_output
        self.input_technology = input_technology.lower()
        self.output_technology = output_technology.lower()
        self.efficiency = efficiency
        self.max_power = max_power
        self.input_active_power = 0.0  # Active power on input side (W)
        self.input_reactive_power = 0.0  # Reactive power on input side (VAR)
        self.output_active_power = 0.0  # Active power on output side (W)
        self.output_reactive_power = 0.0  # Reactive power on output side (VAR)
        self._validate_technologies()

    def _validate_technologies(self):
        """Validate input and output technologies."""
        valid_technologies = {"ac", "dc"}
        if self.input_technology not in valid_technologies:
            raise ValueError(f"input_technology must be one of {valid_technologies}, got {self.input_technology}")
        if self.output_technology not in valid_technologies:
            raise ValueError(f"output_technology must be one of {valid_technologies}, got {self.output_technology}")
        # Phase type validation for AC sides
        if (self.input_technology == "ac" or self.output_technology == "ac") and self.phase_type not in {"single", "three"}:
            raise ValueError("AC sides require phase_type 'single' or 'three'")

    def set_input_power(self, active_power, reactive_power=0.0):
        """Set the input power, adjusting output power with efficiency."""
        if abs(active_power) > self.max_power:
            raise ValueError(f"Input active power {active_power} exceeds max_power {self.max_power}")
        
        self.input_active_power = float(active_power)
        if self.input_technology == "ac":
            self.input_reactive_power = float(reactive_power)
        elif reactive_power != 0:
            raise ValueError("DC input cannot have reactive power")
        
        # Calculate output active power with efficiency
        direction = 1 if active_power >= 0 else -1  # Preserve power flow direction
        self.output_active_power = self.input_active_power * self.efficiency * direction
        
        # Reactive power on output depends on technology and control
        if self.output_technology == "ac":
            self.output_reactive_power = float(self.output_reactive_power)  # Maintain unless set separately
        elif self.output_reactive_power != 0:
            raise ValueError("DC output cannot have reactive power")

    def set_output_reactive_power(self, reactive_power):
        """Set reactive power on the output side (AC only)."""
        if self.output_technology == "dc":
            raise ValueError("DC output cannot have reactive power")
        self.output_reactive_power = float(reactive_power)

    def get_power(self, side="output"):
        """Return power for specified side: 'input' or 'output'."""
        if self.status == "off":
            return 0.0 if (side == "input" and self.input_technology == "dc") or \
                          (side == "output" and self.output_technology == "dc") else complex(0, 0)
        if side == "input":
            if self.input_technology == "dc":
                return self.input_active_power
            return complex(self.input_active_power, self.input_reactive_power)
        elif side == "output":
            if self.output_technology == "dc":
                return self.output_active_power
            return complex(self.output_active_power, self.output_reactive_power)
        raise ValueError("Side must be 'input' or 'output'")

    def get_current(self, voltage, side="output"):
        """Calculate current for specified side."""
        if self.status=="off" or voltage == 0:
            return 0.0 if (side == "input" and self.input_technology == "dc") or \
                          (side == "output" and self.output_technology == "dc") else complex(0, 0)
        power = self.get_power(side)
        if (side == "input" and self.input_technology == "dc") or \
           (side == "output" and self.output_technology == "dc"):
            return power / voltage
        return power / voltage.conjugate()

    def get_status(self):
        """Return inverter status."""
        base_status = super().get_status()
        base_status.update({
            "bus_input": self.bus_input.id,
            "bus_output": self.bus_output.id,
            "input_technology": self.input_technology,
            "output_technology": self.output_technology,
            "input_active_power": self.input_active_power,
            "input_reactive_power": self.input_reactive_power if self.input_technology == "ac" else None,
            "output_active_power": self.output_active_power,
            "output_reactive_power": self.output_reactive_power if self.output_technology == "ac" else None,
            "efficiency": self.efficiency,
            "max_power": self.max_power
        })
        return base_status

    def connect_to_bus(self, bus, side="input"):
        """Connect to a bus on the specified side."""
        if side == "input":
            self.bus_input = bus
            self.bus = bus  # Update base class bus for compatibility
            # print(f"{self.id} input side connected to bus {bus.id}")
            # print_message_network(f"{self.id} input side connected to bus {bus.id}")
        elif side == "output":
            self.bus_output = bus
            # print(f"{self.id} output side connected to bus {bus.id}")
            # print_message_network(f"{self.id} output side connected to bus {bus.id}")
        else:
            raise ValueError("Side must be 'input' or 'output'")