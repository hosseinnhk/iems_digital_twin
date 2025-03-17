import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import numpy as np

# Sample network data (can be replaced with user input or file data)
network_data = {
    'buses': ['Bus 1', 'Bus 2', 'Bus 3', 'Bus 4', 'Bus 5', 'Bus 6', 'Bus 7', 'Bus 8', 'Bus 9'],
    'bus_orientation': "vertical",  # Horizontal or vertical bus orientation
    'lines': [
        ('Bus 1', 'Bus 4', '230 kV'),  # Line 1-4 (root to Bus 4)
        ('Bus 4', 'Bus 5', '18 kV'),   # Line 4-5
        ('Bus 4', 'Bus 6', '18 kV'),   # Line 4-6
        ('Bus 5', 'Bus 7', '18 kV'),   # Line 5-7
        ('Bus 6', 'Bus 9', '18 kV'),   # Line 6-9
        ('Bus 7', 'Bus 8', '230 kV'),  # Line 7-8
        ('Bus 8', 'Bus 9', '230 kV'),  # Line 8-9
        ('Bus 9', 'Bus 2', '16.5 kV'),  # Line 9-2
        ('Bus 2', 'Bus 3', '16.5 kV'),  # Line 2-3
    ],
    'components': [
        ('G1', 'Bus 1', 'Grid'),           # Grid at Bus 1 (root)
        ('T1', 'Bus 1', 'Transformer'),    # Transformer at Bus 1
        ('G2', 'Bus 2', 'Grid'),           # Grid at Bus 2
        ('T2', 'Bus 2', 'Transformer'),    # Transformer at Bus 2
        ('Load A', 'Bus 5', 'Load'),       # Load at Bus 5
        ('Load B', 'Bus 6', 'Load'),       # Load at Bus 6
        ('Load C', 'Bus 8', 'Load'),       # Load at Bus 8
        ('PV farm A', 'Bus 3', 'PV'),      # PV at Bus 3
        ('G3', 'Bus 9', 'Grid'),           # Grid at Bus 9
        ('T3', 'Bus 9', 'Transformer'),    # Transformer at Bus 9
    ],
    'root_bus': 'Bus 1'  # Define the root bus for the tree
}

# Voltage level to color mapping
voltage_colors = {
    '230 kV': 'red',
    '18 kV': 'green',
    '16.5 kV': 'blue'
}

# Component type to color mapping
component_colors = {
    'PV': 'green',
    'Energy Storage': 'blue',
    'Grid': 'orange',
    'Load': 'black',
    'EV Charger': 'black',
    'Heat Pump': 'black',
    'Transformer': 'black'
}

# Create a directed graph
G = nx.DiGraph()

# Add buses as nodes
G.add_nodes_from(network_data['buses'])

# Add lines as edges with voltage attribute
for u, v, voltage in network_data['lines']:
    G.add_edge(u, v, voltage=voltage)

# Custom hierarchical layout function
def get_hierarchical_positions(G, root):
    pos = {root: (0, 0)}  # Start with root at origin
    levels = {root: 0}
    queue = [root]
    level_width = {}
    max_depth = 0

    while queue:
        current = queue.pop(0)
        current_level = levels[current]
        max_depth = max(max_depth, current_level)

        # Get children
        children = [n for n in G.neighbors(current) if n not in pos or levels[n] <= current_level]
        if children:
            level_width[current_level] = level_width.get(current_level, 0) + 1
            base_x = pos[current][0] - (len(children) - 1) * 0.5  # Center children
            for i, child in enumerate(children):
                pos[child] = (base_x + i, current_level + 1)
                levels[child] = current_level + 1
                queue.append(child)

    # Normalize positions
    for node in pos:
        x, y = pos[node]
        pos[node] = (x * 1.5, -y * 1.5)  # Scale and invert y for top-down tree
    return pos

# Get hierarchical positions with Bus 1 as root
pos = get_hierarchical_positions(G, network_data['root_bus'])

# Create the plot
fig, ax = plt.subplots(figsize=(12, 8))

# Draw the hierarchical bus lines (thick red lines)
for u, v in G.edges():
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    # Draw thick red line for buses (simplified as edges for now)
    if network_data['bus_orientation'] == 'horizontal' and abs(x2 - x1) > abs(y2 - y1):
        ax.plot([x1, x2], [y1, y1], color='red', linewidth=6, zorder=1)  # Horizontal bus
        ax.plot([x2, x2], [y1, y2], color='red', linewidth=6, zorder=1)  # Vertical connection
    else:
        ax.plot([x1, x1], [y1, y2], color='red', linewidth=6, zorder=1)  # Vertical bus
        ax.plot([x1, x2], [y2, y2], color='red', linewidth=6, zorder=1)  # Horizontal connection

# Draw bus nodes
for bus, (x, y) in pos.items():
    circle = Circle((x, y), 0.05, fill=True, color='white', edgecolor='black', zorder=3)
    ax.add_patch(circle)
    ax.text(x, y + 0.15, bus, ha='center', va='bottom', fontsize=8, zorder=4)

# Custom function to draw orthogonal edges (lines)
def draw_orthogonal_edge(ax, pos, u, v, color='black'):
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    if abs(x1 - x2) > abs(y1 - y2):
        mid_x = (x1 + x2) / 2
        ax.plot([x1, mid_x], [y1, y1], color=color, linewidth=2, zorder=2)
        ax.plot([mid_x, mid_x], [y1, y2], color=color, linewidth=2, zorder=2)
        ax.plot([mid_x, x2], [y2, y2], color=color, linewidth=2, zorder=2)
        ax.arrow(x2 - 0.05 * (x2 - mid_x) / abs(x2 - mid_x), y2, 0.01 * (x2 - mid_x) / abs(x2 - mid_x), 0, head_width=0.05, head_length=0.1, fc=color, ec=color, zorder=2)
    else:
        mid_y = (y1 + y2) / 2
        ax.plot([x1, x1], [y1, mid_y], color=color, linewidth=2, zorder=2)
        ax.plot([x1, x2], [mid_y, mid_y], color=color, linewidth=2, zorder=2)
        ax.plot([x2, x2], [mid_y, y2], color=color, linewidth=2, zorder=2)
        ax.arrow(x2, y2 - 0.05 * (y2 - mid_y) / abs(y2 - mid_y), 0, 0.01 * (y2 - mid_y) / abs(y2 - mid_y), head_width=0.05, head_length=0.1, fc=color, ec=color, zorder=2)

# Draw edges with voltage-based colors
for u, v, data in G.edges(data=True):
    voltage = data['voltage']
    color = voltage_colors.get(voltage, 'black')
    draw_orthogonal_edge(ax, pos, u, v, color=color)

# Dynamically place components
component_offsets = {}
for comp, bus, comp_type in network_data['components']:
    x, y = pos[bus]
    if bus not in component_offsets:
        component_offsets[bus] = []
    n_comps = len(component_offsets[bus])
    offset_x = -0.5 if n_comps % 2 == 0 else 0.5
    offset_y = -0.3 * (n_comps // 2 + 1)
    component_offsets[bus].append((comp, comp_type))
    
    comp_x, comp_y = x + offset_x, y + offset_y
    color = component_colors.get(comp_type, 'black')
    
    if comp_type == 'Grid':
        ax.text(comp_x, comp_y, 'G', ha='center', va='center', fontsize=8, bbox=dict(facecolor='white', edgecolor=color, boxstyle='circle'))
        ax.plot([comp_x, comp_x], [comp_y + 0.1, comp_y + 0.3], color=color, zorder=2)
        ax.plot([comp_x - 0.05, comp_x + 0.05], [comp_y + 0.3, comp_y + 0.3], color=color, linewidth=2, zorder=2)
        ax.text(comp_x, comp_y + 0.4, comp, ha='center', va='top', fontsize=8, color=color, zorder=3)
    elif comp_type == 'Transformer':
        ax.plot([comp_x, comp_x], [comp_y - 0.05, comp_y + 0.05], color=color, zorder=2)
        ax.add_patch(Circle((comp_x, comp_y + 0.03), 0.03, fill=False, edgecolor=color, zorder=2))
        ax.add_patch(Circle((comp_x, comp_y - 0.03), 0.03, fill=False, edgecolor=color, zorder=2))
        ax.text(comp_x, comp_y + 0.15, comp, ha='center', va='bottom', fontsize=8, color=color, zorder=3)
    elif comp_type in ['Load', 'EV Charger', 'Heat Pump']:
        ax.add_patch(Rectangle((comp_x - 0.15, comp_y - 0.15), 0.3, 0.15, fill=False, edgecolor=color, zorder=2))
        ax.plot([comp_x - 0.1, comp_x + 0.1], [comp_y - 0.075, comp_y - 0.075], color=color, linewidth=2, zorder=2)
        ax.plot([comp_x, comp_x], [comp_y, comp_y - 0.15], color=color, zorder=2)
        ax.text(comp_x, comp_y - 0.25, comp, ha='center', va='top', fontsize=8, color=color, zorder=3)
    elif comp_type == 'PV':
        ax.add_patch(Rectangle((comp_x - 0.15, comp_y - 0.15), 0.3, 0.3, fill=False, edgecolor=color, zorder=2))
        ax.text(comp_x, comp_y, 'PV', ha='center', va='center', fontsize=8, color=color, zorder=3)
        ax.text(comp_x, comp_y - 0.25, comp, ha='center', va='top', fontsize=8, color=color, zorder=3)
        ax.plot([x, comp_x], [y, comp_y], color=color, zorder=2)
    elif comp_type == 'Energy Storage':
        ax.add_patch(Rectangle((comp_x - 0.15, comp_y - 0.15), 0.3, 0.15, fill=False, edgecolor=color, zorder=2))
        ax.plot([comp_x - 0.1, comp_x - 0.1], [comp_y, comp_y - 0.15], color=color, zorder=2)
        ax.plot([comp_x - 0.15, comp_x - 0.05], [comp_y - 0.05, comp_y - 0.05], color=color, linewidth=2, zorder=2)
        ax.plot([comp_x - 0.13, comp_x - 0.07], [comp_y - 0.1, comp_y - 0.1], color=color, linewidth=1, zorder=2)
        ax.text(comp_x, comp_y - 0.25, comp, ha='center', va='top', fontsize=8, color=color, zorder=3)

# Add labels for lines
for u, v, data in G.edges(data=True):
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    label = f"Line {u.split()[1]}-{v.split()[1]}"
    ax.text(mid_x, mid_y + 0.1, label, ha='center', va='bottom', fontsize=8, zorder=3)

# Add legend for voltage levels
legend_elements = [plt.Line2D([0], [0], color=color, lw=2, label=voltage) for voltage, color in voltage_colors.items()]
ax.legend(handles=legend_elements, title="Voltage Level", loc='upper left', bbox_to_anchor=(-0.3, 1))

# Set plot limits and remove axes
x_vals = [coord[0] for coord in pos.values()]
y_vals = [coord[1] for coord in pos.values()]
ax.set_xlim(min(x_vals) - 1, max(x_vals) + 1)
ax.set_ylim(min(y_vals) - 1, max(y_vals) + 1)
ax.axis('off')

plt.title("Building Electricity Network (IEEE Standards - Tree Hierarchy)", fontsize=12, pad=20)
plt.show()