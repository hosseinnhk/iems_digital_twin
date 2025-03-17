from rich.console import Console
from rich.theme import Theme
from rich.table import Table
from rich.text import Text

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "success": "green",
    "init": "orange_red1",
    "error": "red",
    "title": "bold magenta",
    "bus": "blue",
    "component": "green",
    "value": "white"
})

console = Console(theme=custom_theme)

def print_message_network(message):
    # Print initial additions and connections
    def print_addition(message):
        console.print(f"[success]✓ {message}[/]")
        console.print("+------------------------------------+")
    
    def print_connection(message):
        console.print(f"[info]↔ {message}[/]")
    
    def print_status(message):
        console.print(f"[warning]⚡ {message}[/]")
    
    def print_initialized(message):
        console.print(f"[init]⌀ {message}[/]")  
        

    if "Added" in message:
        print_addition(message)
    elif any(word in message for word in ["connected", "Connected"]):
        print_connection(message)
    elif "Initialized" in message:
        print_initialized(message)
    elif "must" in message:
        print_status(message)
    else:
        console.print(message)

def print_network_status(network):

    # Print power status in a table
    table = Table(title="Power Status", title_style="title")
    table.add_column("title", style="component")
    table.add_column("technology", style="value")
    table.add_column("voltage", style="value")
    table.add_column("connected components", style="component")

    for bus_id, bus in network.buses.items():
        print(bus.components)
        components = ", ".join([f"{comp}" for comp in bus.components]) or "None"
        table.add_row(
            bus_id,
            bus.technology,
            str(bus.nominal_voltage),
            components
        )
    console.print(table)
        
    # power_status = [
    #     ("Storage", "charged, SoC: 0.65, Power: -800.0 W"),
    #     ("PV", "generated: 1800.0 W"),
    #     ("Heat Pump", "thermal output: 7000.0 W"),
    #     ("EV", "charging, SoC: 0.62, Power: 5000.0 W"),
    #     # Add more status lines as needed
    # ]

    # for component, status in power_status:
    #     table.add_row(component, status)

    # console.print(table)

    # # Print network status in a structured format
    # console.print("\n[title]Network Status Details[/title]")
    # for bus, details in network_status.items():
    #     console.print(f"\n[bus]{bus}[/]:")
    #     for key, value in details.items():
    #         if key == "connected_components":
    #             console.print(f"  {key}:")
    #             for comp in value:
    #                 console.print(f"    - [component]{comp}[/]")
    #         else:
    #             console.print(f"  {key}: [value]{value}[/]")

# # Your network status dictionary
# network_status = {
#     'DC_Bus1': {'id': 'DC_Bus1', 'technology': 'dc', 'phase_type': 'single', 'nominal_voltage': 48.0, 'current_voltage': 48.0, 'connected_components': [], 'power_balance': 0.0},
#     'DC_Bus2': {'id': 'DC_Bus2', 'technology': 'dc', 'phase_type': 'single', 'nominal_voltage': 48.0, 'current_voltage': 48.0, 'connected_components': [('Inv1', 'input'), ('Battery1', None), ('PV1', None)], 'power_balance': 2000.0},
#     'AC_Bus1': {'id': 'AC_Bus1', 'technology': 'ac', 'phase_type': 'single', 'nominal_voltage': 230.0, 'current_voltage': 230.0, 'connected_components': [('Load1', None), ('Inv1', 'output'), ('Grid1', None), ('HP1', None), ('EV1', None)], 'power_balance': (7050+1500j)}
# }

# Call the function with your data
if __name__ == "__main__":
    print_network_status(network_status)