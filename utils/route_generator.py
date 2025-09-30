import os
import random
import subprocess
import sys
import xml.etree.ElementTree as ET
import yaml

def remove_u_turns(route_file):
    """
    Parses a route file and removes any trips that are U-turns
    (e.g., from 'N_in' to 'N_out').
    """
    tree = ET.parse(route_file)
    root = tree.getroot()
    
    u_turn_trips_found = 0
    for trip in root.findall('trip'):
        from_edge = trip.get('from')
        to_edge = trip.get('to')
        
        # Check if the base name of the edges is the same (e.g., 'N' in 'N_in' and 'N_out')
        if from_edge.split('_')[0] == to_edge.split('_')[0]:
            root.remove(trip)
            u_turn_trips_found += 1
            
    if u_turn_trips_found > 0:
        print(f"  -> Removed {u_turn_trips_found} U-turn trip(s) from {os.path.basename(route_file)}")

    tree.write(route_file)


def generate_routes(config, num_routes, prefix):
    """Generates a number of random route files for training or testing."""
    
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
        
        # Generate background traffic using a compatible flag
        subprocess.run([
            sys.executable, random_trips_path,
            "-n", net_file,
            "-o", route_file_path,
            "-e", str(simulation_end),
            "-p", str(period),
            "--random",
            "--remove-loops" # Use the compatible flag
        ], check=True)

        # Manually filter out any remaining U-turns
        remove_u_turns(route_file_path)
        
        if random.uniform(0, 1) < ambulance_ratio:
            add_ambulance_to_route(route_file_path)

    print(f"\nSuccessfully generated and cleaned {num_routes} new route files in '{route_folder}'.")


def add_ambulance_to_route(route_file):
    """Parses an existing route file and adds a valid ambulance trip."""
    tree = ET.parse(route_file)
    root = tree.getroot()

    if root.find(".//vType[@id='AMBULANCE']") is None:
        ET.SubElement(root, 'vType', id="AMBULANCE", vClass="emergency", speedFactor="1.5", accel="4.0", decel="7.0", color="255,0,0", guiShape="emergency")

    from_edges = ["N_in", "S_in", "E_in", "W_in"]
    to_edges = ["N_out", "S_out", "E_out", "W_out"]
    
    from_edge = random.choice(from_edges)
    
    direction = from_edge.split('_')[0]
    possible_to_edges = [edge for edge in to_edges if direction not in edge]
    to_edge = random.choice(possible_to_edges)

    ET.SubElement(root, 'trip', {
        'id': 'ambulance_trip',
        'type': 'AMBULANCE',
        'from': from_edge,
        'to': to_edge,
        'depart': str(random.randint(10, 50))
    })

    tree.write(route_file)


if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'config.yaml')

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Could not find config.yaml at {config_path}")
        sys.exit(1)
    
    print("Generating training routes...")
    generate_routes(config, config['routes']['num_train_routes'], 'train')
    
    print("\nGenerating testing routes...")
    generate_routes(config, config['routes']['num_test_routes'], 'test')