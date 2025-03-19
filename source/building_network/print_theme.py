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
    table = Table(title="Building Electricity Network", title_style="title")
    table.add_column("title", style="component")
    table.add_column("technology", style="value")
    table.add_column("voltage", style="value")
    table.add_column("connected components", style="component")

    for bus_id, bus in network.buses.items():
        components = ", ".join([f"{comp.id} ({comp.__class__.__name__.lower()})" for comp, _ in bus.components]) or "None"

        table.add_row(
            bus_id,
            bus.technology,
            str(bus.nominal_voltage),
            components
        )
    console.print(table)
          
    from collections import defaultdict
    
    components_by_class = defaultdict(list)
    for comp in network.components:
        components_by_class[comp.__class__].append(comp)

    for comp_class, comps in components_by_class.items():
        table = Table(title=f"{comp_class.__name__} Overview", title_style="title")
        specific_attributes = set()
        table.add_column("ID", style="component")
        
        for comp in comps:
            
            specific_attributes.update(vars(comp).keys())
            discard_attributes = {"id","bus", "type"}
            specific_attributes-=discard_attributes

            
        for attr in sorted(specific_attributes):
            table.add_column(attr, style="value")
        
        for comp in comps:    
            row_data = [
            str(comp.id),
            ]
            for attr in sorted(specific_attributes):
                row_data.append(str(getattr(comp, attr, "")))
            table.add_row(*row_data)  
             
        console.print(table)
