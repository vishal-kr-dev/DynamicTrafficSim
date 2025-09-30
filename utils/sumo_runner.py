import os
import sys
import traci

def start_simulation(config, route_file, use_gui=False):
    """Starts a SUMO simulation using TraCI."""
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("Please declare the environment variable 'SUMO_HOME'")
        
    sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui' if use_gui else 'sumo')

    sumo_cmd = [
        sumo_binary,
        "-c", config['sumo']['config_file'],
        "-r", route_file,
        "--no-warnings", "true"
    ]
    
    traci.start(sumo_cmd)

def close_simulation():
    """Closes the TraCI connection."""
    if traci.isLoaded():
        traci.close()