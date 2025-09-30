import os
import random
import subprocess
import sys
import xml.etree.ElementTree as ET

def generate_routes(config, num_routes, prefix):
    """Generates a number of random route files for training or testing."""
    
    # Ensure SUMO_HOME is set
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("Please declare the environment variable 'SUMO_HOME'")
        
    random_trips_path = os.path.join(tools, "randomTrips.py")
    net_file = config['sumo']['net_file']
    route_folder = config['sumo']['route_folder']
    simulation_end = config['sumo']['simulation_end']
    period = config['routes']['period']
    ambulance_ratio = config['routes']['ambulance_ratio']

    if not os.path.exists(route_folder):
        os.makedirs(route_folder)

    for i in range(num_routes):
        route_file_path = os.path.join(route_folder, f"{prefix}_{i}.rou.xml")
        
        # Generate background traffic
        subprocess.run([
            sys.executable, random_trips_path,
            "-n", net_file,
            "-o", route_file_path,
            "-e", str(simulation_end),
            "-p", str(period),
            "--random", "true"
        ], check=True)
        
        # Add an ambulance to a subset of routes
        if random.uniform(0, 1) < ambulance_ratio:
            add_ambulance_to_route(route_file_path)

    print(f"Successfully generated {num_routes} route files in '{route_folder}'.")

def add_ambulance_to_route(route_file):
    """Parses an existing route file and adds an ambulance trip."""
    tree = ET.parse(route_file)
    root = tree.getroot()

    # Define ambulance vehicle type
    ET.SubElement(root, 'vType', id="AMBULANCE", vClass="emergency", speedFactor="1.5", accel="4.0", decel="7.0", color="255,0,0", guiShape="emergency")

    # Get all edge IDs from the network to define a random route
    edges = ["N_in", "S_in", "E_in", "W_in", "-N_in", "-S_in", "-E_in", "-W_in"]
    from_edge = random.choice(edges)
    to_edge = random.choice([e for e in edges if e != from_edge])

    # Add the ambulance trip
    ET.SubElement(root, 'trip', {
        'id': 'ambulance_trip',
        'type': 'AMBULANCE',
        'from': from_edge,
        'to': to_edge,
        'depart': str(random.randint(10, 50)) # Depart early in the simulation
    })

    tree.write(route_file)

if __name__ == '__main__':
    import yaml
    with open('../config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Generate routes for training and testing
    generate_routes(config, config['routes']['num_train_routes'], 'train')
    generate_routes(config, config['routes']['num_test_routes'], 'test')