from .electrical_component import ElectricalComponent

class Load (ElectricalComponent):
    def __init__(self, id, bus, active_power=0.0, reactive_power=0.0, status="on", flexibility_type= "shiftable", max_shiftable_time=0.0,technology="ac",):
        """
        Initialize a generic load connected to a bus.
        
        Parameters:
        - id (str): Unique identifier.
        - bus (Bus): Bus to which the load is connected.
        - active_power (float): Active power consumption in watts.
        - reactive_power (float): Reactive power consumption in VAR.
        - status (str): "on" or "off" to indicate operational status.
        - flexibility_type (str): Type of load flexibility (e.g., "shiftable", "curtailable").
        - max_shiftable_time (float): Maximum flexibility in minutes for shiftabel loads.
        """
        self.bus = bus
        self.active_power = active_power
        self.reactive_power = reactive_power
        self.status = status.lower()
        self.flexibility_type = flexibility_type.lower()
        self.max_shiftable_time = max_shiftable_time
        
        super().__init__(id, bus, type="load", active_power=active_power, reactive_power=reactive_power, status=status, technology=technology)
        self._validate_inputs()
        
    def _validate_inputs(self):
        """Validate active and reactive power values."""
        if self.active_power < 0:
            raise ValueError(f"Active power must be non-negative, got {self.active_power}")
        if self.reactive_power < 0:
            raise ValueError(f"Reactive power must be non-negative, got {self.reactive_power}")
        if self.flexibility_type not in {"shiftable", "curtailable"}:
            raise ValueError(f"flexibility_type must be 'shiftable' or 'curtailable', got {self.flexibility_type}")
        if self.flexibility_type == "shiftable" and self.max_shiftable_time == 0:
            raise ValueError("max_shiftable_time must be none zero for shiftable loads")
            
    def get_status(self):
        """Return the load status."""
        base_status = super().get_status()
        base_status.update({"flexibility_type": self.flexibility_type, "max_shiftable_time": self.max_shiftable_time})
        return base_status

