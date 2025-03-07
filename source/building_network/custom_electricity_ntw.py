import numpy as np

# Base class for all electircal components
class ElectricalComponent:
    def __init__(self, id, bus, phase_type="single"):
        self.id = id
        self.bus = bus
        self.phase_type = phase_type

    def get_power(self):
        raise NotImplementedError("Subclasses must implement get_power()")

# Bus class
class Bus:
    def __init__(self, id, voltage=230.0):  # Default 230V for single-phase
        self.id = id
        self.voltage = voltage
        self.connected_components = []

    def add_component(self, component):
        self.connected_components.append(component)

    def calculate_power_balance(self):
        total_power = complex(0, 0)  # Active (real) + Reactive (imaginary)
        for component in self.connected_components:
            total_power += component.get_power()
        return total_power

# Load class
class Load(ElectricalComponent):
    def __init__(self, id, bus, power_demand):
        super().__init__(id, bus, "single")
        self.power_demand = power_demand  # Complex number (P + jQ)

    def get_power(self):
        return -self.power_demand  # Negative because it's consuming

# PV class
class PV(ElectricalComponent):
    def __init__(self, id, bus, power_output):
        super().__init__(id, bus, "single")
        self.power_output = power_output  # Complex number (P + jQ)

    def get_power(self):
        return self.power_output  # Positive because it's generating

# Grid class
class Grid(ElectricalComponent):
    def __init__(self, id, bus, max_power):
        super().__init__(id, bus, "single")
        self.max_power = max_power

    def get_power(self):
        # For initial balance calculation, assume grid contributes nothing
        # Actual balancing happens in run_simulation
        return complex(0, 0)

    def supply_power(self, required_power):
        # Supplies or absorbs power to balance the bus, up to max_power
        if abs(required_power) <= abs(self.max_power):
            return required_power
        else:
            raise ValueError(f"Required power {required_power} exceeds grid max_power {self.max_power}")

# Network class
class Network:
    def __init__(self):
        self.buses = []
        self.components = []

    def add_bus(self, bus):
        self.buses.append(bus)

    def add_component(self, component):
        self.components.append(component)
        component.bus.add_component(component)

    def run_simulation(self):
        for bus in self.buses:
            # Calculate power imbalance without grid contribution
            power_balance = bus.calculate_power_balance()
            print(f"Bus {bus.id} power balance before grid: {power_balance}")
            
            # Find grid component and balance the power
            for component in bus.connected_components:
                if isinstance(component, Grid):
                    grid_power = component.supply_power(-power_balance)  # Negative to balance
                    print(f"Grid {component.id} supplies/absorbs: {grid_power}")
                    break

# Example usage
if __name__ == "__main__":
    # Create network
    network = Network()

    # Create bus
    bus1 = Bus(id="Bus1", voltage=230.0)
    network.add_bus(bus1)

    # Create components
    load1 = Load(id="Load1", bus=bus1, power_demand=complex(1000, 200))  # 1000W + 200VAR
    pv1 = PV(id="PV1", bus=bus1, power_output=complex(800, 0))  # 800W
    grid1 = Grid(id="Grid1", bus=bus1, max_power=complex(10000, 0))  # 10kW max

    # Add components to network
    network.add_component(load1)
    network.add_component(pv1)
    network.add_component(grid1)

    # Run simulation
    network.run_simulation()