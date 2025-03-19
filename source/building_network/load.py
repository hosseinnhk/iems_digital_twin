from .electrical_component import ElectricalComponent

class Load (ElectricalComponent):
    def __init__(self, id, bus, active_power=0.0, reactive_power=0.0, status="on", flexibility_type= "nonshiftable", max_shiftable_time=0.0,technology="ac", phase_type="single",
                 voltage_rating=None):
        """
        Initialize a generic load connected to a bus.
        
        Parameters:
        - flexibility_type (str): Type of load flexibility (e.g., "shiftable", "nonshiftable").
        - max_shiftable_time (float): Maximum flexibility in minutes for shiftabel loads.
        """
        self.flexibility_type = flexibility_type.lower()
        self.max_shiftable_time = max_shiftable_time
        
        super().__init__(id, bus, type="load", active_power=active_power, reactive_power=reactive_power, status=status.lower(), technology=technology.lower(), 
                         voltage_rating=voltage_rating, phase_type=phase_type.lower())
        self._validate_inputs()
        
    def _validate_inputs(self):
        if self.active_power < 0:
            raise ValueError(f"Active power must be non-negative, got {self.active_power}")
        if self.reactive_power < 0:
            raise ValueError(f"Reactive power must be non-negative, got {self.reactive_power}")
        if self.flexibility_type not in {"shiftable", "nonshiftable"}:
            raise ValueError(f"flexibility_type must be 'shiftable' or nonshiftable', got {self.flexibility_type}")
        if self.flexibility_type == "shiftable" and self.max_shiftable_time == 0:
            raise ValueError("max_shiftable_time must be none zero for shiftable loads")
        if self.phase_type not in {"single", "three"}:
            raise ValueError(f"phase_type must be 'single' or 'three', got {self.phase_type}")
            
    def get_status(self):
        base_status = super().get_status()
        base_status.update({"flexibility_type": self.flexibility_type, "max_shiftable_time": self.max_shiftable_time})
        return base_status

