# source/building_network/electrical_component.py
class ElectricalComponent:
    def __init__(self, id, bus, phase_type="single", type="load", technology="ac", 
                 voltage_rating=None, active_power=0.0, reactive_power=0.0, active=True):
        self.id = id
        self.bus = bus
        self.phase_type = phase_type.lower()
        self.type = type.lower()
        self.technology = technology.lower()
        self.voltage_rating = voltage_rating
        self.active_power = float(active_power)
        self.reactive_power = float(reactive_power)
        self.active = active
        self._validate_inputs()

    def _validate_inputs(self):
        valid_phase_types = {"single", "three"}
        valid_technologies = {"ac", "dc"}
        valid_types = {"load", "generator", "storage", "grid", "inverter"} 
        if self.phase_type not in valid_phase_types:
            raise ValueError(f"phase_type must be one of {valid_phase_types}, got {self.phase_type}")
        if self.technology not in valid_technologies:
            raise ValueError(f"technology must be one of {valid_technologies}, got {self.technology}")
        if self.type not in valid_types:
            raise ValueError(f"type must be one of {valid_types}, got {self.type}")
        if self.technology == "dc" and self.phase_type == "three":
            raise ValueError("DC components cannot be three-phase")
        if self.technology == "dc" and self.reactive_power != 0:
            raise ValueError("DC components cannot have reactive power")

    def get_power(self):
        if not self.active:
            return 0.0 if self.technology == "dc" else complex(0, 0)
        if self.technology == "dc":
            return self.active_power
        return complex(self.active_power, self.reactive_power)

    def get_current(self, voltage):
        if not self.active or voltage == 0:
            return 0.0 if self.technology == "dc" else complex(0, 0)
        power = self.get_power()
        if self.technology == "dc":
            return power / voltage
        return power / voltage.conjugate()

    def set_active(self, active):
        self.active = bool(active)
        print(f"{self.id} set to {'active' if self.active else 'inactive'}")

    def set_power(self, active_power=None, reactive_power=None):
        if active_power is not None:
            self.active_power = float(active_power)
        if reactive_power is not None:
            if self.technology == "dc":
                raise ValueError("DC components cannot have reactive power")
            self.reactive_power = float(reactive_power)

    def get_status(self):
        return {
            "id": self.id,
            "active": self.active,
            "phase_type": self.phase_type,
            "type": self.type,
            "technology": self.technology,
            "active_power": self.active_power,
            "reactive_power": self.reactive_power if self.technology == "ac" else None
        }

    def connect_to_bus(self, bus):
        self.bus = bus
        print(f"{self.id} connected to bus {bus.id}")