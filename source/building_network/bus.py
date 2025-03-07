# source/building_network/bus.py

class Bus:
    def __init__(self, id, technology="ac", phase_type="single", nominal_voltage=230.0):
        """
        Initialize a bus as a connection point in the electrical network.
        
        Parameters:
        - id (str): Unique identifier for the bus.
        - technology (str): "ac" or "dc" for the bus's electrical system.
        - phase_type (str): "single" or "three" for AC buses; must be "single" for DC.
        - nominal_voltage (float or tuple): Rated voltage (e.g., 230V for single-phase, 
          (230, 400) for 3-phase line-to-neutral and line-to-line).
        """
        self.id = id
        self.technology = technology.lower()
        self.phase_type = phase_type.lower()
        self.nominal_voltage = nominal_voltage  # Float for DC/single-phase, tuple for 3-phase
        self.components = []  # List of connected ElectricalComponents or Inverters
        self.voltage = self.nominal_voltage  # Current voltage (updated during simulation)
        self._validate_inputs()

    def _validate_inputs(self):
        """Validate technology and phase_type consistency."""
        valid_technologies = {"ac", "dc"}
        valid_phase_types = {"single", "three"}
        
        if self.technology not in valid_technologies:
            raise ValueError(f"technology must be one of {valid_technologies}, got {self.technology}")
        if self.phase_type not in valid_phase_types:
            raise ValueError(f"phase_type must be one of {valid_phase_types}, got {self.phase_type}")
        if self.technology == "dc" and self.phase_type == "three":
            raise ValueError("DC buses cannot be three-phase")
        if isinstance(self.nominal_voltage, tuple) and self.technology == "dc":
            raise ValueError("DC buses must have a single nominal voltage, not a tuple")
        if isinstance(self.nominal_voltage, tuple) and self.phase_type != "three":
            raise ValueError("Tuple voltage is only valid for three-phase buses")

    def connect_component(self, component, side=None):
        """
        Connect an ElectricalComponent or Inverter to this bus.
        
        Parameters:
        - component: Instance of ElectricalComponent or Inverter.
        - side (str, optional): For Inverters, "input" or "output"; None for single-bus components.
        """
        from .inverter import Inverter  # Import here to avoid circular import
        
        if isinstance(component, Inverter):
            if side not in {"input", "output"}:
                raise ValueError("Inverter connection requires side='input' or 'output'")
            component.connect_to_bus(self, side)
        else:
            component.connect_to_bus(self)
        
        # Validate technology compatibility
        component_technology = component.input_technology if isinstance(component, Inverter) and side == "input" else \
                              component.output_technology if isinstance(component, Inverter) and side == "output" else \
                              component.technology
        if component_technology != self.technology:
            raise ValueError(f"Component {component.id} technology ({component_technology}) "
                            f"does not match bus {self.id} technology ({self.technology})")
        
        self.components.append((component, side))
        print(f"Connected {component.id} to bus {self.id}" + (f" ({side} side)" if side else ""))

    def get_power_balance(self):
        """
        Calculate the net power balance at this bus.
        - Positive power: Into the bus (e.g., from generators).
        - Negative power: Out of the bus (e.g., to loads).
        Returns float for DC, complex for AC single-phase, or tuple for 3-phase (future).
        """
        if not self.components:
            return 0.0 if self.technology == "dc" else complex(0, 0)
        
        total_power = 0.0 if self.technology == "dc" else complex(0, 0)
        from .inverter import Inverter
        
        for component, side in self.components:
            if isinstance(component, Inverter):
                power = component.get_power(side="input" if side == "input" else "output")
                # Input side: power into bus; Output side: power out of bus
                total_power += power if side == "input" else -power
            else:
                # Single-bus components: positive for generation, negative for consumption
                power = component.get_power()
                total_power += power
        
        return total_power

    def set_voltage(self, voltage):
        """Update the bus voltage (for simulation purposes)."""
        self.voltage = voltage
        print(f"Bus {self.id} voltage set to {voltage}")

    def get_status(self):
        """Return the bus status."""
        return {
            "id": self.id,
            "technology": self.technology,
            "phase_type": self.phase_type,
            "nominal_voltage": self.nominal_voltage,
            "current_voltage": self.voltage,
            "connected_components": [(comp.id, side) for comp, side in self.components],
            "power_balance": self.get_power_balance()
        }