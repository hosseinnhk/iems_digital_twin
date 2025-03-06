# import pypsa
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta

class BuildingNetwork:
    def __init__(self, voltage_level=0.4):  # 400V line-to-line
        """Initialize a 3-phase building electrical network in PyPSA."""
        self.net = pypsa.Network()
        self.voltage_level = voltage_level  # in kV (0.4 kV = 400 V)
        
class BuildingPowerFlowSimulator:
    def __init__(self, pv_capacity=10, storage_capacity=20, load_peak=15):
        """
        Initialize the building power flow simulator.
        
        Parameters:
        - pv_capacity (float): PV system capacity in kW
        - storage_capacity (float): Battery storage capacity in kWh
        - load_peak (float): Peak load demand in kW
        """
        self.pv_capacity = pv_capacity  # kW
        self.storage_capacity = storage_capacity  # kWh
        self.load_peak = load_peak  # kW
        self.network = None
        self.timesteps = pd.date_range(
            start="2025-03-06 00:00",
            end="2025-03-06 23:59",
            freq="1min"
        )  # 1440 minutes in a day
        self.setup_network()

#         # Grid bus (3-phase)
#         self.grid_bus = self.add_bus("Grid Bus", v_nom=self.voltage_level)
#         # External grid modeled as a slack generator
#         self.net.add("Generator", "External Grid", bus=self.grid_bus, p_set=0, control="Slack", v_set=1.0)

#         # Main distribution bus (3-phase)
#         self.main_bus = self.add_bus("Main Bus")
#         self.add_line(self.grid_bus, self.main_bus)

#         # Phase-specific buses
#         self.bus_l1 = self.add_bus("Bus L1")
#         self.bus_l2 = self.add_bus("Bus L2")
#         self.bus_l3 = self.add_bus("Bus L3")

#         # Connect phase buses to main bus (short lines simulating distribution)
#         self.add_line(self.main_bus, self.bus_l1, length_km=0.0005, name="Line L1")
#         self.add_line(self.main_bus, self.bus_l2, length_km=0.0005, name="Line L2")
#         self.add_line(self.main_bus, self.bus_l3, length_km=0.0005, name="Line L3")

#         # Dictionaries to track loads (optional, for your bookkeeping)
#         self.threephase_loads = {}
#         self.singlephase_loads = {}

#     def add_bus(self, name="Bus", v_nom=None):
#         """Add a bus to the network."""
#         v_nom = v_nom or self.voltage_level
#         self.net.add("Bus", name, v_nom=v_nom)
#         return name  # PyPSA uses bus names as identifiers

#     def add_line(self, from_bus, to_bus, length_km=0.01, name=None):
#         """Add a line between two buses with default electrical parameters."""
#         if name is None:
#             name = f"Line {from_bus} to {to_bus}"
#         # Typical parameters for a short 400V line (adjust as needed)
#         r_per_km = 0.207  # Ohm/km (example for copper cable)
#         x_per_km = 0.08   # Ohm/km (example inductive reactance)
#         self.net.add("Line", name, bus0=from_bus, bus1=to_bus, length=length_km,
#                      r=r_per_km * length_km, x=x_per_km * length_km)

#     def add_load(self, bus, p_kw, q_kvar=0, name="Load", phase="L1"):
#         """Add a single-phase load to a specific phase."""
#         phase_map = {"L1": 1, "L2": 2, "L3": 3}
#         if phase not in phase_map:
#             raise ValueError("Phase must be 'L1', 'L2', or 'L3'")
        
#         # PyPSA uses MW and Mvar, so convert kW/kvar to MW/Mvar
#         p_mw = p_kw / 1000
#         q_mvar = q_kvar / 1000
        
#         # Add the load to the specified bus (phase-specific)
#         load_name = f"{name} {phase}"
#         self.net.add("Load", load_name, bus=bus, p_set=p_mw, q_set=q_mvar)
#         self.singlephase_loads[load_name] = {"bus": bus, "phase": phase}
#         return load_name
    
#     def add_3phase_load(self, p_kw, q_kvar=0, name="3ph Load"):
#         """Add a symmetric 3-phase load as three identical single-phase loads."""
#         p_kw_per_phase = p_kw / 3
#         q_kvar_per_phase = q_kvar / 3  # Assuming symmetric reactive power; adjust if needed
#         phase_buses = [("L1", self.bus_l1), ("L2", self.bus_l2), ("L3", self.bus_l3)]
        
#         # Add a load to each phase bus
#         load_names = [
#             self.add_load(bus, p_kw_per_phase, q_kvar_per_phase, name=f"{name}_L{phase}", phase=phase)
#             for phase, bus in phase_buses
#         ]
        
#         # Store the list of load names in threephase_loads
#         self.threephase_loads[name] = load_names
#         return name

#     def remove_3phase_load(self, name):
#         """Remove a 3-phase load by deleting its three single-phase components."""
#         if name not in self.threephase_loads:
#             raise ValueError(f"No 3-phase load named '{name}' found")
        
#         # Drop the loads from the network using their names
#         self.net.loads.drop(self.threephase_loads[name], inplace=True)
#         del self.threephase_loads[name]

#     def add_1phase_load(self, p_kw, q_kvar=0, name="Load", phase="L1"):
#         """Add a single-phase load to a specific phase."""
#         phase_buses = {"L1": self.bus_l1, "L2": self.bus_l2, "L3": self.bus_l3}
#         if phase not in phase_buses:
#             raise ValueError("Phase must be 'L1', 'L2', or 'L3'")
        
#         # Add the load and store its name
#         load_name = self.add_load(phase_buses[phase], p_kw, q_kvar, name=name, phase=phase)
#         self.singlephase_loads[name] = load_name
#         return name

#     def remove_1phase_load(self, name):
#         """Remove a single-phase load by name."""
#         if name not in self.singlephase_loads:
#             raise ValueError(f"No single-phase load named '{name}' found")
        
#         # Drop the load from the network using its name
#         self.net.loads.drop(self.singlephase_loads[name], inplace=True)
#         del self.singlephase_loads[name]

#     def add_pv(self, p_kw=0, q_kvar=0, name="PV System", phase="3ph", efficiency=0.97):
#         """Add a PV system (single-phase or 3-phase) with inverter efficiency."""
#         if not 0 < efficiency <= 1:
#             raise ValueError("Efficiency must be between 0 and 1")
#         p_kw_ac = p_kw * efficiency  # Convert DC power to AC power after efficiency loss
        
#         if phase == "3ph":
#             # 3-phase PV: split power equally across L1, L2, L3
#             p_kw_per_phase = p_kw_ac / 3
#             q_kvar_per_phase = q_kvar / 3  # Assuming symmetric reactive power; adjust if needed
#             phase_buses = [("L1", self.bus_l1), ("L2", self.bus_l2), ("L3", self.bus_l3)]
#             pv_names = [
#                 f"{name}_L{phase}" for phase, bus in phase_buses
#             ]
#             for (phase, bus), pv_name in zip(phase_buses, pv_names):
#                 self.net.add("Generator", pv_name, bus=bus, p_set=p_kw_per_phase / 1000, 
#                             q_set=q_kvar_per_phase / 1000)
#             # Initialize threephase_pvs dictionary if not present
#             self.threephase_pvs = getattr(self, 'threephase_pvs', {})
#             self.threephase_pvs[name] = pv_names
#         else:
#             # Single-phase PV
#             phase_map = {"L1": self.bus_l1, "L2": self.bus_l2, "L3": self.bus_l3}
#             if phase not in phase_map:
#                 raise ValueError("Phase must be '3ph', 'L1', 'L2', or 'L3'")
#             p_mw_ac = p_kw_ac / 1000
#             q_mvar = q_kvar / 1000
#             self.net.add("Generator", name, bus=phase_map[phase], p_set=p_mw_ac, q_set=q_mvar)
#             # Initialize singlephase_pvs dictionary if not present
#             self.singlephase_pvs = getattr(self, 'singlephase_pvs', {})
#             self.singlephase_pvs[name] = name
        
#         return name

#     def remove_pv(self, name, phase="3ph"):
#         """Remove a PV system by name and phase type."""
#         if phase == "3ph":
#             if not hasattr(self, 'threephase_pvs') or name not in self.threephase_pvs:
#                 raise ValueError(f"No 3-phase PV system named '{name}' found")
#             # Drop all three phase PV generators by their names
#             self.net.generators.drop(self.threephase_pvs[name], inplace=True)
#             del self.threephase_pvs[name]
#         else:
#             if not hasattr(self, 'singlephase_pvs') or name not in self.singlephase_pvs:
#                 raise ValueError(f"No single-phase PV system named '{name}' found")
#             # Drop the single-phase PV generator by its name
#             self.net.generators.drop(self.singlephase_pvs[name], inplace=True)
#             del self.singlephase_pvs[name]
            
#     def add_storage(self, p_kw, max_e_mwh, name="Battery", phase="3ph"):
#         """Add an energy storage system (single-phase or 3-phase)."""
#         if phase == "3ph":
#             # 3-phase storage: split power and energy equally across L1, L2, L3
#             p_kw_per_phase = p_kw / 3
#             max_e_mwh_per_phase = max_e_mwh / 3
#             phase_buses = [("L1", self.bus_l1), ("L2", self.bus_l2), ("L3", self.bus_l3)]
#             storage_names = [
#                 f"{name}_L{phase}" for phase, bus in phase_buses
#             ]
#             for (phase, bus), storage_name in zip(phase_buses, storage_names):
#                 self.net.add("StorageUnit", storage_name, bus=bus, 
#                             p_nom=p_kw_per_phase / 1000,  # Nominal power in MW
#                             max_e=max_e_mwh_per_phase,    # Max energy in MWh
#                             p_set=0)                      # Initial power setpoint (can be time-varying)
#             # Initialize threephase_storage dictionary if not present
#             self.threephase_storage = getattr(self, 'threephase_storage', {})
#             self.threephase_storage[name] = storage_names
#         else:
#             # Single-phase storage
#             phase_map = {"L1": self.bus_l1, "L2": self.bus_l2, "L3": self.bus_l3}
#             if phase not in phase_map:
#                 raise ValueError("Phase must be '3ph', 'L1', 'L2', or 'L3'")
#             p_mw = p_kw / 1000
#             self.net.add("StorageUnit", name, bus=phase_map[phase], 
#                         p_nom=p_mw,            # Nominal power in MW
#                         max_e=max_e_mwh,       # Max energy in MWh
#                         p_set=0)               # Initial power setpoint
#             # Initialize singlephase_storage dictionary if not present
#             self.singlephase_storage = getattr(self, 'singlephase_storage', {})
#             self.singlephase_storage[name] = name
#         return name

#     def remove_storage(self, name, phase="3ph"):
#         """Remove an energy storage system by name and phase type."""
#         if phase == "3ph":
#             if not hasattr(self, 'threephase_storage') or name not in self.threephase_storage:
#                 raise ValueError(f"No 3-phase storage system named '{name}' found")
#             # Drop all three phase storage units by their names
#             self.net.storage_units.drop(self.threephase_storage[name], inplace=True)
#             del self.threephase_storage[name]
#         else:
#             if not hasattr(self, 'singlephase_storage') or name not in self.singlephase_storage:
#                 raise ValueError(f"No single-phase storage system named '{name}' found")
#             # Drop the single-phase storage unit by its name
#             self.net.storage_units.drop(self.singlephase_storage[name], inplace=True)
#             del self.singlephase_storage[name]
            
#     def add_line(self, from_bus, to_bus, length_km=0.001, name="Line"):
#         """Add a line between two buses with parameters based on NAYY 4x50 SE cable."""
#         # Electrical parameters for NAYY 4x50 SE (approximate values for 400V aluminum cable)
#         r_per_km = 0.641  # Resistance in Ω/km
#         x_per_km = 0.08   # Reactance in Ω/km (estimated for low-voltage cable)

#         # Calculate total resistance and reactance based on length
#         r = r_per_km * length_km
#         x = x_per_km * length_km

#         # Add the line to the network
#         self.net.add("Line", name, bus0=from_bus, bus1=to_bus, length=length_km, r=r, x=x)
#         return name

#     def run_power_flow(self):
#         """Run a static AC power flow simulation and return results."""
#         # Run AC power flow for the current snapshot
#         self.net.pf()
        
#         # Return results for buses, lines, and loads
#         # For a static simulation, use the static DataFrames with computed values
#         res_bus = self.net.buses  # Voltage magnitudes and angles are updated here
#         res_line = self.net.lines  # Line flows are updated here
#         res_load = self.net.loads  # Load power consumption (static values unless time-varying)
        
#         # Include additional results from the power flow (e.g., p, q at buses and lines)
#         res_bus = self.net.buses.assign(
#             p_mw=self.net.res_bus.p,  # Active power at buses
#             q_mvar=self.net.res_bus.q  # Reactive power at buses
#         )
#         res_line = self.net.lines.assign(
#             p0_mw=self.net.res_line.p0,  # Active power at bus0
#             q0_mvar=self.net.res_line.q0,  # Reactive power at bus0
#             p1_mw=self.net.res_line.p1,  # Active power at bus1
#             q1_mvar=self.net.res_line.q1   # Reactive power at bus1
#         )
        
#         return res_bus, res_line, res_load


# # Example usage (assuming the rest of the class is defined)
# if __name__ == "__main__":
#     building = BuildingNetwork(voltage_level=0.4)
    
#     # Add some components for testing
#     building.add_3phase_load(p_kw=30, q_kvar=6, name="Motor")
#     building.add_pv(p_kw=15, q_kvar=0, name="Solar Array", phase="3ph", efficiency=0.95)
#     building.add_storage(p_kw=10, max_e_mwh=0.05, name="Battery", phase="3ph")
    
#     # Run power flow
#     res_bus, res_line, res_load = building.run_power_flow()
    
#     print("Bus Results:")
#     print(res_bus[['v_nom', 'p_mw', 'q_mvar']])
#     print("\nLine Results:")
#     print(res_line[['r', 'x', 'p0_mw', 'q0_mvar', 'p1_mw', 'q1_mvar']])
#     print("\nLoad Results:")
#     print(res_load[['bus', 'p_set', 'q_set']])


# # import pypsa

# # # create a new network
# # n = pypsa.Network()
# # n.add("Bus", "mybus")
# # n.add("Load", "myload", bus="mybus", p_set=100)
# # n.add("Generator", "mygen", bus="mybus", p_nom=100, marginal_cost=20)

# # # load an example network
# # n = pypsa.examples.ac_dc_meshed()

# # # run the optimisation
# # n.optimize()

# # # plot results
# # n.generators_t.p.plot()
# # n.plot()

# # # get statistics
# # n.statistics()
# # n.statistics.energy_balance()


import pypsa
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class BuildingPowerFlowSimulator:
    def __init__(self, pv_capacity=10, storage_capacity=20, load_peak=15):
        """
        Initialize the building power flow simulator.
        
        Parameters:
        - pv_capacity (float): PV system capacity in kW
        - storage_capacity (float): Battery storage capacity in kWh
        - load_peak (float): Peak load demand in kW
        """
        self.pv_capacity = pv_capacity  # kW
        self.storage_capacity = storage_capacity  # kWh
        self.load_peak = load_peak  # kW
        self.network = None
        self.timesteps = pd.date_range(
            start="2025-03-06 00:00",
            end="2025-03-06 23:59",
            freq="1min"
        )  # 1440 minutes in a day
        self.setup_network()

    def generate_synthetic_profiles(self):
        """Generate synthetic time series for PV and load."""
        # Time in hours for PV generation (sinusoidal pattern)
        hours = np.linspace(0, 24, len(self.timesteps))
        pv_profile = self.pv_capacity * np.sin(np.pi * hours / 12) * (hours > 6) * (hours < 18)
        pv_profile = np.clip(pv_profile, 0, self.pv_capacity)  # Limit to capacity

        # Load profile: base load with peaks in morning and evening
        load_profile = self.load_peak * (0.5 + 0.3 * np.sin(np.pi * hours / 12) + 
                                        0.2 * np.sin(2 * np.pi * hours / 12))
        load_profile = np.clip(load_profile, 0, self.load_peak * 1.2)

        return pv_profile, load_profile

    def setup_network(self):
        """Set up the PyPSA network with components."""
        self.network = pypsa.Network()
        self.network.set_snapshots(self.timesteps)

        # Buses
        self.network.add("Bus", "building_bus", v_nom=230)  # Main building bus (low voltage)
        self.network.add("Bus", "grid_bus", v_nom=230)      # Grid connection bus

        # Grid connection (via a link)
        self.network.add("Link", "grid_link", 
                         bus0="grid_bus", 
                         bus1="building_bus", 
                         p_nom=100,  # Large capacity to allow free flow
                         efficiency=0.98)

        # Generator: PV system
        pv_profile, _ = self.generate_synthetic_profiles()
        self.network.add("Generator", "pv", 
                         bus="building_bus", 
                         p_nom=self.pv_capacity, 
                         p_max_pu=pv_profile / self.pv_capacity,
                         marginal_cost=0.01)  # Small cost to prefer PV usage

        # Load
        _, load_profile = self.generate_synthetic_profiles()
        self.network.add("Load", "building_load", 
                         bus="building_bus", 
                         p_set=load_profile)

        # Energy Storage (Battery)
        self.network.add("Store", "battery", 
                         bus="building_bus", 
                         e_nom=self.storage_capacity, 
                         e_cyclic=True,  # Cyclic state of charge (start = end)
                         e_initial=self.storage_capacity * 0.5,  # Start at 50% charge
                         marginal_cost=0.05)  # Small cost to optimize usage

        # External Grid as a generator with high cost
        self.network.add("Generator", "grid_supply", 
                         bus="grid_bus", 
                         p_nom=1000,  # Large capacity
                         marginal_cost=0.1)  # Higher cost to prioritize local resources

    def run_simulation(self):
        """Run the power flow simulation and optimization."""
        # Optimize the network (linear optimal power flow)
        self.network.optimize(solver_name="glpk")  # Use GLPK solver (install via: pip install pyomo glpk)
        print("Simulation completed successfully.")

    def get_results(self):
        """Extract and return simulation results."""
        if self.network is None or not hasattr(self.network, "objective"):
            raise ValueError("Run the simulation first using run_simulation().")

        results = {
            "pv_generation": self.network.generators_t.p["pv"],
            "load_demand": self.network.loads_t.p_set["building_load"],
            "battery_state": self.network.stores_t.e["battery"],
            "grid_import_export": self.network.links_t.p0["grid_link"],  # Positive = import, negative = export
            "grid_supply": self.network.generators_t.p["grid_supply"]
        }
        return pd.DataFrame(results, index=self.timesteps)

    def plot_results(self):
        """Plot the simulation results (requires matplotlib)."""
        import matplotlib.pyplot as plt

        results = self.get_results()
        plt.figure(figsize=(12, 6))
        plt.plot(results.index, results["pv_generation"], label="PV Generation (kW)")
        plt.plot(results.index, results["load_demand"], label="Load Demand (kW)")
        plt.plot(results.index, results["battery_state"], label="Battery State (kWh)")
        plt.plot(results.index, results["grid_import_export"], label="Grid Import/Export (kW)")
        plt.xlabel("Time")
        plt.ylabel("Power (kW) or Energy (kWh)")
        plt.title("Building Power Flow Simulation - 1 Day, 1-Min Resolution")
        plt.legend()
        plt.grid(True)
        plt.show()


# Example usage
if __name__ == "__main__":
    # Create simulator instance
    simulator = BuildingPowerFlowSimulator(pv_capacity=10, storage_capacity=20, load_peak=15)

    # Run the simulation
    simulator.run_simulation()

    # Get and display results
    results = simulator.get_results()
    print(results.head())

    # Plot results
    simulator.plot_results()
