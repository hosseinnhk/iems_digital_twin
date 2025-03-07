# source/building_network/network.py
import networkx as nx
import matplotlib.pyplot as plt
from .bus import Bus
from .electrical_component import ElectricalComponent
from .inverter import Inverter
from .line import Line

class Network:
    def __init__(self):
        """Initialize an empty electrical network."""
        self.buses = {}
        self.components = []
        self.inverters = []
        self.lines = []  # New list for lines

    def add_bus(self, bus):
        """Add a bus to the network."""
        if not isinstance(bus, Bus):
            raise ValueError("Must be an instance of Bus")
        self.buses[bus.id] = bus
        print(f"Added bus {bus.id} to network")

    def add_component(self, component):
        """Add an ElectricalComponent, Inverter, or Line to the network."""
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
            self.buses[component.bus.id].connect_component(component)
        else:
            raise ValueError("Must be an ElectricalComponent, Inverter, or Line")
        print(f"Added {component.id} to network")

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
        nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=2000)
        
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
        return {bus_id: bus.get_status() for bus_id, bus in self.buses.items()}