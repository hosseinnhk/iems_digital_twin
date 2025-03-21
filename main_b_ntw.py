# iems_digital_twin/main.py
from source.building_network import Inverter, Bus, EnergyStorage, Line, Grid, PV, HeatPump, EVCharger, Network, Load

if __name__ == "__main__":

    # Create network
    network = Network()

    # Add buses
    dc_bus1 = Bus(id="DC_Bus1", technology="dc", nominal_voltage=48.0)
    dc_bus2 = Bus(id="DC_Bus2", technology="dc", nominal_voltage=48.0)
    ac_bus = Bus(id="AC_Bus1", technology="ac", nominal_voltage=230.0, phase_type="three")
    network.add_bus(dc_bus1)
    network.add_bus(dc_bus2)
    network.add_bus(ac_bus)
    
    # Add grid
    grid = Grid(
        id="Grid1",
        bus=ac_bus,
        max_power=10000.0,
        voltage=230.0,
        technology="ac",
        phase_type= "three"
    )
    
    # Add components
    load = Load(
        id="Phone charger",
        bus=ac_bus,
        technology="ac",
        active_power=10.0,
        reactive_power=20.0,
        flexibility_type="shiftable",
        max_shiftable_time=60.0,
        phase_type="single",
        voltage_rating=230.0
    )  
    
    load2 = Load(
        id="Oven",
        bus=ac_bus,
        technology="ac",
        active_power=2000.0,
        reactive_power=200.0,
        flexibility_type="nonshiftable",
        phase_type="three",
        voltage_rating=130.0
    )  
    
    inv = Inverter(
        id="Inv1",
        bus_input=dc_bus2,
        bus_output=ac_bus,
        input_technology="dc",
        output_technology="ac",
        phase_type= "three",
        efficiency=0.95
    )
    
    inv2 = Inverter(
        id="Inv2",
        bus_input=dc_bus2,
        bus_output=ac_bus,
        input_technology="dc",
        output_technology="ac",
        efficiency=0.95
    )
    
    storage = EnergyStorage(
        id="Battery1",
        bus=dc_bus2,
        capacity=5000.0,
        initial_soc=0.5,
        max_charge_power=1000.0,
        max_discharge_power=1000.0,
        technology="dc",
        voltage_rating=48.0
    )
      
    pv = PV(
        id="PV1",
        bus=dc_bus2,
        max_power=2000.0,
        efficiency=0.18,
        area=10.0,
        technology="dc",
        voltage_rating=48.0
    )
    
    heat_pump = HeatPump(
        id="HP1",
        bus=ac_bus,
        rated_power=2500.0,
        cop=3.5,
        mode="heating",
        technology="ac",
        voltage_rating=230.0
    )
    
    heat_pump_2 = HeatPump(
        id="HP2",
        bus=ac_bus,
        rated_power=2200.0,
        cop=2.5,
        mode="heating",
        technology="ac",
        phase_type="three",
        voltage_rating=130.0
    )
    
    ev_charger = EVCharger(
        id="EV1",
        bus=ac_bus,
        max_charge_power=7000.0,  # 7 kW charging
        max_discharge_power=7000.0,  # 7 kW V2B/V2G
        efficiency=0.95,
        ev_capacity=40000.0,  # 40 kWh battery
        initial_soc=0.5,
        technology="ac",
        voltage_rating=230.0
    )
    
    #Add line
    line = Line(
        id="Line1",
        bus_from=dc_bus1,
        bus_to=dc_bus2,
        length=10.0,
        resistance=0.05,
        technology="dc"
    )

    network.add_component(grid)
    network.add_component(load)
    network.add_component(load2)
    network.add_component(inv)
    network.add_component(inv2)
    network.add_component(storage)
    network.add_component(line)
    network.add_component(pv)
    network.add_component(heat_pump)
    network.add_component(heat_pump_2)
    network.add_component(ev_charger)

    # network.print_summary()
    # Simulate behavior
    storage.charge(1000.0, time_step=1.0)
    # print(f"Storage charged, SoC: {storage.soc:.2f}, Power: {storage.get_power()}")
    pv_power = pv.generate_power(irradiance=1000.0)
    # print(f"PV generated: {pv_power} W")
    thermal_output = heat_pump.set_operating_condition(power_fraction=0.8)
    # print(f"Heat Pump thermal output: {thermal_output} W")
    ev_charge_power = ev_charger.charge(5000.0, time_step=1.0)  # Charge at 5 kW
    # print(f"EV charging, SoC: {ev_charger.soc:.2f}, Power: {ev_charge_power} W")
    inv.set_input_power(1000.0)
    inv.set_output_reactive_power(100.0)
    ac_bus_balance = ac_bus.get_power_balance()
    grid_power = grid.supply_power(-ac_bus_balance)
    # print(f"AC Bus balance before grid: {ac_bus_balance}")
    # print(f"Grid supplies/absorbs: {grid_power}")

    # # Simulate V2B/V2G
    ev_discharge_power = ev_charger.discharge(3000.0, time_step=1.0)  # Discharge 3 kW
    # print(f"EV discharging (V2B/V2G), SoC: {ev_charger.soc:.2f}, Power: {ev_discharge_power} W")
    ac_bus_balance = ac_bus.get_power_balance()
    grid_power = grid.supply_power(-ac_bus_balance)
    # print(f"AC Bus balance after V2B: {ac_bus_balance}")
    # print(f"Grid supplies/absorbs after V2B: {grid_power}")

    # # Print network status
    print("Network Status:", network.get_status())
    # print(network.components)

    # Visualize
    # network.visualize()