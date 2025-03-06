import pandapower as pp
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class BuildingNetwork:
    def __init__(self, voltage_level=0.4):  # 400V line-to-line
        """Initialize a 3-phase building electrical network."""
        self.net = pp.create_empty_network()
        self.voltage_level = voltage_level
        # Grid bus (3-phase)
        self.grid_bus = pp.create_bus(self.net, vn_kv=voltage_level, name="Grid Bus", type="b")
        pp.create_ext_grid(self.net, bus=self.grid_bus, vm_pu=1.0, name="External Grid")
        # Main distribution bus (3-phase)
        self.main_bus = self.add_bus("Main Bus")
        self.add_line(self.grid_bus, self.main_bus)
        # Phase-specific buses
        self.bus_l1 = self.add_bus("Bus L1")
        self.bus_l2 = self.add_bus("Bus L2")
        self.bus_l3 = self.add_bus("Bus L3")
        # Connect phase buses to main bus (short lines simulating distribution)
        self.add_line(self.main_bus, self.bus_l1, length_km=0.0005, name="Line L1")
        self.add_line(self.main_bus, self.bus_l2, length_km=0.0005, name="Line L2")
        self.add_line(self.main_bus, self.bus_l3, length_km=0.0005, name="Line L3")
        
        self.threephase_loads = {}
        self.singlephase_loads = {}

    def add_bus(self, name="Bus", vn_kv=None, type="b"):
        vn_kv = vn_kv or self.voltage_level
        return pp.create_bus(self.net, vn_kv=vn_kv, name=name, type=type)
    
    def add_load(self, bus, p_kw, q_kvar=0, name="Load", phase="L1"):
            """Add a single-phase load to a specific phase."""
            phase_map = {"L1": 1, "L2": 2, "L3": 3}
            if phase not in phase_map:
                raise ValueError("Phase must be 'L1', 'L2', or 'L3'")
            return pp.create_load(self.net, bus=bus, p_mw=p_kw/1000, q_mvar=q_kvar/1000, type=f"delta_{phase_map[phase]}", name=name)

    def add_3phase_load(self, p_kw, q_kvar=0, name="3ph Load"):
        """Add a symmetric 3-phase load as three identical single-phase loads."""
        p_kw_per_phase = p_kw / 3
        phase_buses = [("L1", self.bus_l1), ("L2", self.bus_l2), ("L3", self.bus_l3)]
        load_indices = [
            self.add_load(bus, p_kw_per_phase, q_kvar, name=f"{name}_L{phase}", phase=phase)
            for phase, bus in phase_buses
        ]
        self.threephase_loads[name] = load_indices
        return name

    def remove_3phase_load(self, name):
        """Remove a 3-phase load by deleting its three single-phase components."""
        if name not in self.threephase_loads:
            raise ValueError(f"No 3-phase load named '{name}' found")
        self.net.load.drop(self.threephase_loads[name], inplace=True)
        del self.threephase_loads[name]

    def add_1phase_load(self, p_kw, q_kvar=0, name="Load", phase="L1"):
        """Add a single-phase load to a specific phase."""
        phase_buses = {"L1": self.bus_l1, "L2": self.bus_l2, "L3": self.bus_l3}
        if phase not in phase_buses:
            raise ValueError("Phase must be 'L1', 'L2', or 'L3'")
        load_idx = self.add_load(phase_buses[phase], p_kw, q_kvar, name=name, phase=phase)
        self.singlephase_loads[name] = load_idx
        return name

    def remove_1phase_load(self, name):
        """Remove a single-phase load by name."""
        if name not in self.singlephase_loads:
            raise ValueError(f"No single-phase load named '{name}' found")
        self.net.load.drop(self.singlephase_loads[name], inplace=True)
        del self.singlephase_loads[name]

    def add_pv(self, p_kw=0, q_kvar=0, name="PV System", phase="3ph", efficiency=0.97):
        """Add a PV system (single-phase or 3-phase) with inverter efficiency."""
        if not 0 < efficiency <= 1:
            raise ValueError("Efficiency must be between 0 and 1")
        p_kw_ac = p_kw * efficiency  # Convert DC power to AC power after efficiency loss
        
        if phase == "3ph":
            # 3-phase PV: split power equally across L1, L2, L3
            p_kw_per_phase = p_kw_ac / 3
            phase_buses = [("L1", self.bus_l1), ("L2", self.bus_l2), ("L3", self.bus_l3)]
            pv_indices = [
                pp.create_sgen(self.net, bus, p_mw=p_kw_per_phase/1000, q_mvar=q_kvar/1000, name=f"{name}_L{phase}")
                for phase, bus in phase_buses
            ]
            self.threephase_pvs = getattr(self, 'threephase_pvs', {})  # Initialize if not present
            self.threephase_pvs[name] = pv_indices
        else:
            # Single-phase PV
            phase_map = {"L1": self.bus_l1, "L2": self.bus_l2, "L3": self.bus_l3}
            if phase not in phase_map:
                raise ValueError("Phase must be '3ph', 'L1', 'L2', or 'L3'")
            pv_idx = pp.create_sgen(self.net, phase_map[phase], p_mw=p_kw_ac/1000, q_mvar=q_kvar/1000, name=name)
            self.singlephase_pvs = getattr(self, 'singlephase_pvs', {})  # Initialize if not present
            self.singlephase_pvs[name] = pv_idx
        return name

    def remove_pv(self, name, phase="3ph"):
        """Remove a PV system by name and phase type."""
        if phase == "3ph":
            if not hasattr(self, 'threephase_pvs') or name not in self.threephase_pvs:
                raise ValueError(f"No 3-phase PV system named '{name}' found")
            self.net.sgen.drop(self.threephase_pvs[name], inplace=True)
            del self.threephase_pvs[name]
        else:
            if not hasattr(self, 'singlephase_pvs') or name not in self.singlephase_pvs:
                raise ValueError(f"No single-phase PV system named '{name}' found")
            self.net.sgen.drop(self.singlephase_pvs[name], inplace=True)
            del self.singlephase_pvs[name]

    def add_storage(self, p_kw, max_e_mwh, name="Battery", phase="3ph"):
        """Add an energy storage system (single-phase or 3-phase)."""
        
        if phase == "3ph":
            # 3-phase storage: split power equally across L1, L2, L3
            p_kw_per_phase = p_kw / 3
            max_e_mwh_per_phase = max_e_mwh / 3
            phase_buses = [("L1", self.bus_l1), ("L2", self.bus_l2), ("L3", self.bus_l3)]
            storage_indices = [
                pp.create_storage(self.net, bus, p_mw=p_kw_per_phase/1000, max_e_mwh=max_e_mwh_per_phase, 
                                 name=f"{name}_L{phase}")
                for phase, bus in phase_buses
            ]
            self.threephase_storage = getattr(self, 'threephase_storage', {})  # Initialize if not present
            self.threephase_storage[name] = storage_indices
        else:
            # Single-phase storage
            phase_map = {"L1": self.bus_l1, "L2": self.bus_l2, "L3": self.bus_l3}
            if phase not in phase_map:
                raise ValueError("Phase must be '3ph', 'L1', 'L2', or 'L3'")
            storage_idx = pp.create_storage(self.net, phase_map[phase], p_mw=p_kw/1000, max_e_mwh=max_e_mwh, 
                                          name=name)
            self.singlephase_storage = getattr(self, 'singlephase_storage', {})  # Initialize if not present
            self.singlephase_storage[name] = storage_idx
        return name

    def remove_storage(self, name, phase="3ph"):
        """Remove an energy storage system by name and phase type."""
        if phase == "3ph":
            if not hasattr(self, 'threephase_storage') or name not in self.threephase_storage:
                raise ValueError(f"No 3-phase storage system named '{name}' found")
            self.net.storage.drop(self.threephase_storage[name], inplace=True)
            del self.threephase_storage[name]
        else:
            if not hasattr(self, 'singlephase_storage') or name not in self.singlephase_storage:
                raise ValueError(f"No single-phase storage system named '{name}' found")
            self.net.storage.drop(self.singlephase_storage[name], inplace=True)
            del self.singlephase_storage[name]

    def add_line(self, from_bus, to_bus, length_km=0.001, name="Line"):
        return pp.create_line(self.net, from_bus=from_bus, to_bus=to_bus, length_km=length_km,
                              std_type="NAYY 4x50 SE", name=name)

    def run_power_flow(self):
        pp.runpp(self.net, numba=True)
        return self.net.res_bus, self.net.res_line, self.net.res_load


    def __str__(self):
        threephase_pv_count = len(getattr(self, 'threephase_pvs', {}))
        singlephase_pv_count = len(getattr(self, 'singlephase_pvs', {}))
        threephase_storage_count = len(getattr(self, 'threephase_storage', {}))
        singlephase_storage_count = len(getattr(self, 'singlephase_storage', {}))
        return (f"BuildingNetwork with {len(self.net.bus)} buses, "
                f"{len(self.net.load)} loads ({len(self.threephase_loads)} three-phase, "
                f"{len(self.singlephase_loads)} single-phase ),"
                f"{len(self.net.sgen)} PV systems ({threephase_pv_count} three-phase, {singlephase_pv_count} single-phase), "
                f"{len(self.net.storage)} storage units ({threephase_storage_count} three-phase, {singlephase_storage_count} single-phase)")

    def visualize_results(self):
            """Visualize voltage, power flow, and current after running power flow simulation."""
            # Ensure power flow has been run
            if not hasattr(self.net, 'res_bus') or self.net.res_bus.empty:
                raise ValueError("Run power flow simulation first using run_power_flow()")

            # Extract results
            bus_results = self.net.res_bus
            line_results = self.net.res_line

            # Plot 1: Bus Voltages (pu)
            plt.figure(figsize=(10, 5))
            plt.bar(bus_results.index, bus_results['vm_pu'], color='skyblue')
            plt.axhline(y=1.0, color='gray', linestyle='--', label='Nominal Voltage (1.0 pu)')
            plt.title('Bus Voltages (pu)')
            plt.xlabel('Bus Index')
            plt.ylabel('Voltage (pu)')
            plt.xticks(bus_results.index, self.net.bus['name'], rotation=45, ha='right')
            plt.legend()
            plt.tight_layout()
            plt.show()

            # Plot 2: Line Power Flow (MW)
            plt.figure(figsize=(10, 5))
            plt.bar(line_results.index, line_results['p_from_mw'], color='salmon', label='Active Power (from)')
            plt.title('Line Power Flow (MW)')
            plt.xlabel('Line Index')
            plt.ylabel('Active Power (MW)')
            plt.xticks(line_results.index, self.net.line['name'], rotation=45, ha='right')
            plt.legend()
            plt.tight_layout()
            plt.show()

            # Plot 3: Line Current (A)
            # Calculate current: I = P / (sqrt(3) * V * cos(phi)), assuming cos(phi)=1 for simplicity
            line_voltage_kv = self.voltage_level  # e.g., 0.4 kV
            line_currents = (line_results['p_from_mw'] * 1000) / (1.732 * line_voltage_kv)  # Convert MW to kW, assume pf=1
            plt.figure(figsize=(10, 5))
            plt.bar(line_results.index, line_currents, color='lightgreen')
            plt.title('Line Currents (A)')
            plt.xlabel('Line Index')
            plt.ylabel('Current (A)')
            plt.xticks(line_results.index, self.net.line['name'], rotation=45, ha='right')
            plt.tight_layout()
            plt.show()


# Example usage
if __name__ == "__main__":
    # bldg_net = BuildingNetwork()

    # # Add 3-phase loads (split into symmetric single-phase loads)
    # bldg_net.add_3phase_load(p_kw=12, name="Oven")
    # bldg_net.add_3phase_load(p_kw=9, name="Cooktop")
    # bldg_net.add_3phase_load(p_kw=3, name="Washing Machine")

    # # Add single-phase loads to phase-specific buses
    # bldg_net.add_1phase_load(p_kw=6, name="TV", phase="L1")
    # bldg_net.add_1phase_load(p_kw=6, name="Lighting", phase="L2")
    # bldg_net.add_1phase_load(p_kw=6, name="radio", phase="L3")

    # # Add PV and battery systems
    # bldg_net.add_pv(p_kw=5, name="Solar PV 3ph", efficiency=0.96)
    # # Add a single-phase PV (2 kW DC → 1.94 kW AC on L1)
    # bldg_net.add_pv(p_kw=2, name="Solar PV L1", phase="L1", efficiency=0.95)
    # # Add a 3-phase battery (3 kW, 0.01 MWh → 1 kW, 0.00333 MWh per phase)
    # bldg_net.add_storage(p_kw=3, max_e_mwh=0.01, name="Battery 3ph")
    # # Add a single-phase battery (1 kW, 0.005 MWh on L2)
    # bldg_net.add_storage(p_kw=1, max_e_mwh=0.005, name="Battery L2", phase="L2")

    # # Run power flow
    # bus_results, line_results, load_results = bldg_net.run_power_flow()
    
    # # Print initial results
    # print("Initial State:")
    # print(bldg_net)
    # print("Line Results (Loading Percent):\n", line_results['loading_percent'])

    # # Remove a single-phase load
    # bldg_net.remove_1phase_load("TV")
    # bldg_net.run_power_flow()
    # print("\nAfter removing TV:")
    # print(bldg_net)
    # print("Line Results (Loading Percent):\n", bldg_net.net.res_line['loading_percent'])

    # # Remove a 3-phase load
    # bldg_net.remove_3phase_load("Oven")
    # bldg_net.run_power_flow()
    # print("\nAfter removing Oven:")
    # print(bldg_net)
    # print("Line Results (Loading Percent):\n", bldg_net.net.res_line['loading_percent'])

    # # Visualize results
    # bldg_net.visualize_results()
    
