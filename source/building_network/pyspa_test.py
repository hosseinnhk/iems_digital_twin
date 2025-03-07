import pypsa
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class BuildingPowerFlowSimulator:
    def __init__(self, nominal_voltage=230, timesteps=None):

        self.nominal_voltage = nominal_voltage
        self.network = pypsa.Network()
        self.timesteps = timesteps if timesteps is not None else pd.date_range(
            start="2025-03-06 00:00",
            end="2025-03-06 23:59",
            freq="1min"
        )
        self.network.set_snapshots(self.timesteps)
        self.phases = ["A", "B", "C"]
        
        self.loads = {}
        self.pv_systems = {}
        self.storage_units = {}
        
        self.setup_base_network()

    def setup_base_network(self):
        """Set up the base 3-phase network structure."""
        # Grid bus (external connection)
        self.network.add("Bus", "grid_bus", v_nom=self.nominal_voltage * np.sqrt(3))  # Line-to-line voltage

        # Building phase buses
        for phase in self.phases:
            self.network.add("Bus", f"building_bus_phase_{phase}", v_nom=self.nominal_voltage)

        # Grid connection links (3-phase)
        for phase in self.phases:
            self.network.add("Link", f"grid_link_phase_{phase}",
                             bus0="grid_bus",
                             bus1=f"building_bus_phase_{phase}",
                             p_nom=100,  # Large capacity
                             efficiency=0.98)

        # Grid supply (high-cost generator)
        self.network.add("Generator", "grid_supply",
                         bus="grid_bus",
                         p_nom=1000,  # Large capacity
                         marginal_cost=0.5)

    def add_load(self, name, phases, p_set, peak_power=None):
        """
        Add a load to the network (single-phase or 3-phase).
        
        Parameters:
        - name (str): Unique label for the load
        - phases (str or list): "A", "B", "C" for single-phase or ["A", "B", "C"] for 3-phase
        - p_set (float or np.array): Power demand (kW); scalar or time series
        - peak_power (float): Optional peak power for scaling (kW)
        """
        if name in self.loads:
            raise ValueError(f"Load '{name}' already exists.")
        
        if isinstance(phases, str):
            phases = [phases]
        for phase in phases:
            if phase not in self.phases:
                raise ValueError(f"Invalid phase: {phase}. Use 'A', 'B', or 'C'.")

        # Generate synthetic profile if p_set is scalar
        if np.isscalar(p_set):
            hours = np.linspace(0, 24, len(self.timesteps))
            p_set = p_set * (0.5 + 0.3 * np.sin(np.pi * hours / 12) + 
                            0.2 * np.sin(2 * np.pi * hours / 12))
            if peak_power:
                p_set = np.clip(p_set, 0, peak_power)

        # Add load to each specified phase
        for phase in phases:
            load_name = f"{name}_phase_{phase}"
            self.network.add("Load", load_name,
                             bus=f"building_bus_phase_{phase}",
                             p_set=p_set / len(phases))  # Split power across phases
            self.loads[load_name] = {"phases": phases, "p_set": p_set}

    def add_pv(self, name, phases, capacity, pv_profile_pu=None, efficiency=0.98):
        """
        Add a PV system to the network (single-phase or 3-phase).
        
        Parameters:
        - name (str): Unique label for the PV system
        - phases (str or list): "A", "B", "C" or ["A", "B", "C"]
        - capacity (float): PV capacity (kW)
        - pv_profile_pu (np.array): Optional per-unit output profile; defaults to synthetic
        """
        if name in self.pv_systems:
            raise ValueError(f"PV system '{name}' already exists.")
        
        if not 0 <= efficiency <= 1:
            raise ValueError("Efficiency must be between 0 and 1.")
        
        if isinstance(phases, str):
            phases = [phases]
        for phase in phases:
            if phase not in self.phases:
                raise ValueError(f"Invalid phase: {phase}")

        # Synthetic PV profile if not provided
        if pv_profile_pu is None:
            hours = np.linspace(0, 24, len(self.timesteps))
            pv_profile_pu = np.sin(np.pi * hours / 12) * (hours > 6) * (hours < 18)
            pv_profile_pu = np.clip(pv_profile_pu, 0, 1)
            
        pv_profile_pu_eff = pv_profile_pu * efficiency
        
        # Add PV to each specified phase
        for phase in phases:
            pv_name = f"{name}_phase_{phase}"
            self.network.add("Generator", pv_name,
                             bus=f"building_bus_phase_{phase}",
                             p_nom=capacity / len(phases),  # Split capacity
                             p_max_pu=pv_profile_pu_eff,
                             marginal_cost=0.01)
            self.pv_systems[pv_name] = {"phases": phases, "capacity": capacity}

    def add_storage(self, name, phases, capacity, charge_power, discharge_power, e_initial=None, soc_min=0.2, soc_max=1.0, ch_efficiency=0.98, disch_efficiency=0.98):

        if name in self.storage_units:
            raise ValueError(f"Storage unit '{name}' already exists.")
        
        if isinstance(phases, str):
            phases = [phases]
        for phase in phases:
            if phase not in self.phases:
                raise ValueError(f"Invalid phase: {phase}")

        if not (0 <= soc_min <= soc_max <= 1):
            raise ValueError("soc_min and soc_max must be between 0 and 1, with soc_min <= soc_max.")
        if not (0 < ch_efficiency <= 1 and 0 < disch_efficiency <= 1):
            raise ValueError("Charging and discharging efficiencies must be between 0 and 1.")


        e_initial = e_initial if e_initial is not None else capacity * 0.5
        for phase in phases:
            storage_name = f"{name}_phase_{phase}"
            self.network.add("Store", storage_name,
                bus=f"building_bus_phase_{phase}",
                e_nom=capacity / len(phases),  # Split capacity
                e_min=(capacity / len(phases)) * soc_min,  # Minimum energy
                e_max=(capacity / len(phases)) * soc_max,  # Maximum energy
                e_cyclic=True,
                e_initial=e_initial / len(phases),
                p_nom=charge_power / len(phases),  # Max charge power
                p_nom_extendable=False,
                p_max=discharge_power / len(phases),  # Max discharge power (positive)
                p_min=-charge_power / len(phases),
                marginal_cost=0.05,
                charge_efficiency=ch_efficiency,  # PyPSA uses this for charging
                discharge_efficiency=disch_efficiency)  # PyPSA uses this for discharging
            self.storage_units[storage_name] = {
                "phases": phases,
                "capacity": capacity,
                "charge_power": charge_power,
                "discharge_power": discharge_power,
                "soc_min": soc_min,
                "soc_max": soc_max,
                "ch_efficiency": ch_efficiency,
                "disch_efficiency": disch_efficiency
            }
            
    def add_battery(self, name, phases, capacity, charge_power, discharge_power, 
                e_initial=None, soc_min=0.2, soc_max=1.0, ch_efficiency=0.95, disch_efficiency=0.95):
        """
        Add a battery storage unit to the network (single-phase or multi-phase).
        
        Parameters:
        - name (str): Unique label for the battery
        - phases (str or list): "A", "B", "C" or ["A", "B", "C"]
        - capacity (float): Battery energy capacity (kWh)
        - charge_power (float): Maximum charging power (kW)
        - discharge_power (float): Maximum discharging power (kW)
        - e_initial (float): Initial energy (kWh); defaults to 50% of capacity
        - soc_min (float): Minimum state of charge (0 to 1); default 0.2
        - soc_max (float): Maximum state of charge (0 to 1); default 1.0
        - ch_efficiency (float): Charging efficiency (0 to 1); default 0.95
        - disch_efficiency (float): Discharging efficiency (0 to 1); default 0.95
        """
        if name in self.storage_units:
            raise ValueError(f"Battery '{name}' already exists.")
        
        if isinstance(phases, str):
            phases = [phases]
        for phase in phases:
            if phase not in self.phases:
                raise ValueError(f"Invalid phase: {phase}")

        if not (0 <= soc_min <= soc_max <= 1):
            raise ValueError("soc_min and soc_max must be between 0 and 1, with soc_min <= soc_max.")
        if not (0 < ch_efficiency <= 1 and 0 < disch_efficiency <= 1):
            raise ValueError("Charging and discharging efficiencies must be between 0 and 1.")
        if capacity <= 0 or charge_power <= 0 or discharge_power <= 0:
            raise ValueError("Capacity, charge_power, and discharge_power must be positive.")

        # Default initial energy is 50% of capacity if not specified
        e_initial = e_initial if e_initial is not None else capacity * 0.5

        # Add battery as a StorageUnit for each specified phase
        for phase in phases:
            battery_name = f"{name}_phase_{phase}"
            # Split capacity and power across phases
            p_nom = max(charge_power, discharge_power) / len(phases)  # Nominal power is the max of charge/discharge
            max_hours = (capacity / len(phases)) / p_nom  # Energy-to-power ratio
            
            self.network.add("StorageUnit", battery_name,
                            bus=f"building_bus_phase_{phase}",
                            p_nom=p_nom,
                            p_nom_extendable=False,
                            p_min_pu=-charge_power / (p_nom * len(phases)),  # Negative for charging
                            p_max_pu=discharge_power / (p_nom * len(phases)),  # Positive for discharging
                            state_of_charge_initial=e_initial,
                            max_hours=max_hours,
                            # e_initial = e_initial,
                            efficiency_store=ch_efficiency,
                            efficiency_dispatch=disch_efficiency,
                            marginal_cost=0.02,  # Moderate cost to balance usage
                            cyclic_state_of_charge=True)  # SOC returns to initial value over the day
            
            # Store metadata for tracking
            self.storage_units[battery_name] = {
                "phases": phases,
                "capacity": capacity,
                "charge_power": charge_power,
                "discharge_power": discharge_power,
                "soc_min": soc_min,
                "soc_max": soc_max,
                "ch_efficiency": ch_efficiency,
                "disch_efficiency": disch_efficiency
            }            
        
            
 
    def run_simulation(self):
        """Run the power flow simulation with fully integrated storage optimization."""
        # Run the optimization without pre-setting storage dispatch
        self.network.optimize(solver_name="glpk")

        # Optional: Post-optimization adjustment (if specific control is needed)
        # This step is not strictly necessary unless you want to override PyPSA's dispatch
        # for storage_name, attrs in self.storage_units.items():
        #     phase = storage_name.split("_phase_")[-1]
        #     net_power = pd.Series(0.0, index=self.timesteps)
        #     pv_power = sum(self.network.generators_t.p.get(f"{name}_phase_{phase}", 0.0) 
        #                   for name in self.pv_systems)
        #     load_power = sum(self.network.loads_t.p_set.get(f"{name}_phase_{phase}", 0.0) 
        #                     for name in self.loads)
        #     net_power = pv_power - load_power

        #     # Refine storage dispatch based on net power (optional)
        #     p_set = self.network.stores_t.p[storage_name].copy()
        #     for t in self.timesteps:
        #         current_soc = self.network.stores_t.e[storage_name].loc[t] / (attrs["capacity"] / len(attrs["phases"]))
        #         if net_power.loc[t] > 0 and current_soc < attrs["soc_max"]:  # Surplus: charge
        #             p_set.loc[t] = -min(attrs["charge_power"] / len(attrs["phases"]), net_power.loc[t])
        #         elif net_power.loc[t] < 0 and current_soc > attrs["soc_min"]:  # Deficit: discharge
        #             p_set.loc[t] = min(attrs["discharge_power"] / len(attrs["phases"]), -net_power.loc[t])
        #     self.network.stores_t.p[storage_name] = p_set

        print("Simulation completed successfully.")

    def get_results(self):
        """Extract and return simulation results."""
        if not hasattr(self.network, "objective"):
            raise ValueError("Run the simulation first using run_simulation().")

        results = {
            "loads": {name: self.network.loads_t.p_set[name] for name in self.loads},
            "pv_generation": {name: self.network.generators_t.p[name] for name in self.pv_systems},
            # "storage_power": {name: self.network.stores_t.p[name] for name in self.storage_units},
            # "storage_state": {name: self.network.stores_t.e[name] for name in self.storage_units},
            "storage_power": {name: self.network.storage_units_t.p[name] for name in self.storage_units},
            "storage_state": {name: self.network.storage_units_t.state_of_charge[name] for name in self.storage_units},
            "grid_import_export": {f"grid_link_phase_{phase}": self.network.links_t.p0[f"grid_link_phase_{phase}"]
                                   for phase in self.phases},
            "grid_supply": self.network.generators_t.p["grid_supply"]
        }
        return results

    # def plot_results(self):
        """Plot the simulation results."""
        import matplotlib.pyplot as plt

        results = self.get_results()
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 8), sharex=True)

        # Loads
        for name, power in results["loads"].items():
            ax1.plot(self.timesteps, power, label=name)
        ax1.set_ylabel("Power (kW)")
        
        ax1.grid(True)

        # PV Generation
        for name, power in results["pv_generation"].items():
            ax1.plot(self.timesteps, power, label=name)
        for name, power in results["grid_import_export"].items():
            ax1.plot(self.timesteps, power, label=name)
        ax1.legend()
        # ax2.set_ylabel("PV Generation (kW)")
        # ax2.legend()
        # ax2.grid(True)

        # Storage and Grid
        # for name, power in results["storage_power"].items():
        #     ax3.plot(self.timesteps, power, label=f"{name} (Power)")
        for name, energy in results["storage_state"].items():
            ax3.plot(self.timesteps, energy, label=f"{name} (Storage)")
        # for name, power in results["grid_import_export"].items():
        #     ax3.plot(self.timesteps, power, label=name)
        ax3.set_ylabel("Storage (kWh) / Grid (kW)")
        ax3.legend()
        ax3.grid(True)

        plt.xlabel("Time")
        plt.suptitle("Building Power Flow Simulation - 3-Phase System")
        plt.show()


    def plot_results(self):
        """Plot the simulation results, separated by phase."""
        import matplotlib.pyplot as plt

        results = self.get_results()
        fig, axes = plt.subplots(len(self.phases), 1, figsize=(12, 4 * len(self.phases)), sharex=True)

        # Ensure axes is iterable even for a single phase
        if len(self.phases) == 1:
            axes = [axes]

        # Plot each phase separately
        for i, phase in enumerate(self.phases):
            ax = axes[i]
            ax.set_title(f"Phase {phase} Power Flow")

            # Loads for this phase
            for name, power in results["loads"].items():
                if f"_phase_{phase}" in name:
                    ax.plot(self.timesteps, power, label=name)

            # PV Generation for this phase
            for name, power in results["pv_generation"].items():
                if f"_phase_{phase}" in name:
                    ax.plot(self.timesteps, power, label=name)

            # Grid import/export for this phase
            for name, power in results["grid_import_export"].items():
                if f"_phase_{phase}" in name:
                    ax.plot(self.timesteps, power, label=name, linestyle="--")

            # Storage power for this phase
            for name, power in results["storage_power"].items():
                if f"_phase_{phase}" in name:
                    ax.plot(self.timesteps, power, label=f"{name} (Power)", linestyle="-.")

            # Storage state (energy) for this phase - secondary y-axis
            ax2 = ax.twinx()
            for name, energy in results["storage_state"].items():
                if f"_phase_{phase}" in name:
                    ax2.plot(self.timesteps, energy, label=f"{name} (Energy)", color="purple", linestyle=":")
                    ax2.set_ylabel("Storage Energy (kWh)")
                    ax2.yaxis.label.set_color("purple")
                    ax2.tick_params(axis="y", colors="purple")

            # Formatting
            ax.set_ylabel("Power (kW)")
            ax.grid(True)
            ax.legend(loc="upper left")
            ax2.legend(loc="upper right")

        plt.xlabel("Time")
        plt.suptitle("Building Power Flow Simulation - Per Phase", y=1.02)
        plt.tight_layout()
        plt.show()


# Example usage
if __name__ == "__main__":
    # Create simulator instance
    simulator = BuildingPowerFlowSimulator(nominal_voltage=230)

    # Add components
    simulator.add_load("lighting", "A", p_set=5, peak_power=6)  # Single-phase load on Phase A
    simulator.add_load("hvac", ["A", "B", "C"], p_set=12, peak_power=14)  # 3-phase load
    simulator.add_pv("pv_roof", ["A", "B"], capacity=10)  # 2-phase PV
    # simulator.add_storage("battery", ["C"] , capacity=20)  # Single-phase storage on Phase C
    # Add a storage unit
    # simulator.add_storage("battery", "A", capacity=20, ch_efficiency=0.95, disch_efficiency=0.95)
    simulator.add_battery("battery", ["A", "B", "C"], capacity=20, charge_power=5, discharge_power=5, e_initial=10)

    # Run simulation
    simulator.run_simulation()
    results = simulator.get_results()
    
    print("Sample Load Results:")
    for name, power in results["loads"].items():
        print(f"{name}: {power.iloc[0]} kW at t=0")
        
    simulator.plot_results()
