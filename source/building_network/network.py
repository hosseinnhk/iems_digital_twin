# source/building_network/network.py
import networkx as nx
import matplotlib.pyplot as plt
from .bus import Bus
from .electrical_component import ElectricalComponent
from .inverter import Inverter
from .line import Line
from .print_theme import *

class Network:
    def __init__(self):
        """Initialize an empty electrical network."""
        self.buses = {}
        self.components = []
        self.inverters = []
        self.lines = []  # New list for lines
        print_message_network("Initialized an empty network")
        print("+------------------------------------+")

    def add_bus(self, bus):
        """Add a bus to the network."""
        if not isinstance(bus, Bus):
            raise ValueError("Must be an instance of Bus")
        self.buses[bus.id] = bus
        # print(f"Added bus {bus.id} to network")
        print_message_network(f"Added bus {bus.id} to network")

    def add_component(self, component):
        """Add an ElectricalComponent to the network."""
        if isinstance(component, Inverter):
            if component.bus_input.id not in self.buses or component.bus_output.id not in self.buses:
                raise ValueError("Both inverter buses must be added to the network first")
            self.inverters.append(component)
            self.buses[component.bus_input.id].connect_component(component, side="input")
            self.buses[component.bus_output.id].connect_component(component, side="output")
        elif isinstance(component, Line):
            if component.bus_from.id not in self.buses or component.bus_to.id not in self.buses:
                raise ValueError("Both line buses must be added to the network first")
            self.lines.append(component)
        elif isinstance(component, ElectricalComponent):
            if component.bus.id not in self.buses:
                raise ValueError("Component bus must be added to the network first")
            self.components.append(component)
            # self.buses[component.bus.id].components.append(component)
            self.buses[component.bus.id].connect_component(component)
        else:
            raise ValueError("Must be an ElectricalComponent, Inverter, or Line")
        # print(f"Added {component.id} to network")
        print_message_network(f"Added {component.id} to network")


    def print_summary(self):
        from rich.console import Console
        from rich.theme import Theme
        from rich.table import Table
        from rich.text import Text
        
        custom_theme = Theme({
        "info": "cyan",
        "warning": "yellow",
        "success": "green",
        "error": "red",
        "title": "bold magenta",
        "bus": "blue",
        "component": "green",
        "value": "white"
        })
        
        console = Console(theme=custom_theme)
        
        console.print("\n[title]Network Status[/title]")

        # Buses Table
        bus_table = Table(title="Buses", title_style="title")
        bus_table.add_column("ID", style="bus")
        bus_table.add_column("Technology", style="value")
        bus_table.add_column("Voltage", style="value")
        bus_table.add_column("Connected Components", style="component")

        for bus_id, bus in self.buses.items():
            components = ", ".join([f"{comp.id} ({side})" if side else comp.id 
                                  for comp, side in bus.connected_components]) or "None"
            bus_table.add_row(
                bus_id,
                bus.technology,
                str(bus.nominal_voltage),
                components
            )
        console.print(bus_table)

        # Components Table
        comp_table = Table(title="Components", title_style="title")
        comp_table.add_column("ID", style="component")
        comp_table.add_column("Type", style="value")
        comp_table.add_column("Connected Bus", style="bus")

        for comp in self.components:
            comp_table.add_row(
                comp.id,
                comp.__class__.__name__,
                comp.bus.id
            )
        console.print(comp_table)

        # Inverters Table
        if self.inverters:
            inv_table = Table(title="Inverters", title_style="title")
            inv_table.add_column("ID", style="component")
            inv_table.add_column("Input Bus", style="bus")
            inv_table.add_column("Output Bus", style="bus")
            
            for inv in self.inverters:
                inv_table.add_row(
                    inv.id,
                    inv.bus_input.id,
                    inv.bus_output.id
                )
            console.print(inv_table)

        # Lines Table
        if self.lines:
            line_table = Table(title="Lines", title_style="title")
            line_table.add_column("ID", style="component")
            line_table.add_column("From Bus", style="bus")
            line_table.add_column("To Bus", style="bus")
            
            for line in self.lines:
                line_table.add_row(
                    line.id,
                    line.bus_from.id,
                    line.bus_to.id
                )
            console.print(line_table)

        # Summary
        console.print(f"\n[success]Network Summary:[/]")
        console.print(f"  Total Buses: [value]{len(self.buses)}[/]")
        console.print(f"  Total Components: [value]{len(self.components)}[/]")
        console.print(f"  Total Inverters: [value]{len(self.inverters)}[/]")
        console.print(f"  Total Lines: [value]{len(self.lines)}[/]")        
    
    def visualize(self, save_path=None):
        """Visualize the network using NetworkX and Matplotlib."""
        G = nx.Graph()

        # Add buses as nodes
        for bus_id, bus in self.buses.items():
            G.add_node(bus_id, label=f"{bus_id}\n{bus.technology.upper()} {bus.phase_type}")

        # Add inverters as edges
        for inv in self.inverters:
            G.add_edge(inv.bus_input.id, inv.bus_output.id, 
                       label=f"{inv.id}\n{inv.input_technology}->{inv.output_technology}")

        # Add lines as edges
        for line in self.lines:
            G.add_edge(line.bus_from.id, line.bus_to.id, 
                       label=f"{line.id}\n{line.technology.upper()} R={line.resistance}Ω")

        # Add components as node annotations
        pos = nx.spring_layout(G)
        plt.figure(figsize=(12, 8))

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=200)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color="gray", width=2)
        
        # Draw node labels
        node_labels = nx.get_node_attributes(G, "label")
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10)

        # Draw edge labels
        edge_labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

        # Annotate components on their buses
        for comp in self.components:
            bus_pos = pos[comp.bus.id]
            plt.text(bus_pos[0], bus_pos[1] - 0.1, f"{comp.id} ({comp.type})", 
                     ha="center", va="top", fontsize=8, color="darkred")

        plt.title("Building Electricity Network")
        if save_path:
            plt.savefig(save_path)
            print(f"Network visualization saved to {save_path}")
        else:
            plt.show()

    def get_status(self):
        """Return the status of all buses in the network."""
        # return {bus_id: bus.get_status() for bus_id, bus in self.buses.items()}
        print_network_status(self)