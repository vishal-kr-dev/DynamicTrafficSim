import os
import sys
import yaml
import glob

def run_gui_viewer():
    """
    Launches the SUMO GUI to visually inspect a chosen route file.
    """
    # --- 1. Load Configuration ---
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config.yaml not found. Make sure you are in the project's root directory.")
        return

    # --- 2. Find and Select a Route File ---
    route_folder = config['sumo']['route_folder']
    if not os.path.exists(route_folder):
        print(f"Error: Route folder '{route_folder}' not found.")
        print("Please generate routes first using the route generator script.")
        return

    route_files = glob.glob(os.path.join(route_folder, '*.rou.xml'))
    if not route_files:
        print(f"Error: No route files (.rou.xml) found in '{route_folder}'.")
        return

    print("Available route files:")
    for i, file in enumerate(route_files):
        print(f"  [{i}] {os.path.basename(file)}")

    try:
        choice = int(input("Enter the number of the route file to view: "))
        if not 0 <= choice < len(route_files):
            raise ValueError
        chosen_route_file = route_files[choice]
    except (ValueError, IndexError):
        print("Invalid choice. Exiting.")
        return

    # --- 3. Launch SUMO GUI with TraCI ---
    # Ensure SUMO_HOME is set
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("Please declare the environment variable 'SUMO_HOME'")
    
    import traci
    
    sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui')
    sumo_config_file = config['sumo']['config_file']

    sumo_cmd = [
        sumo_binary,
        "-c", sumo_config_file,
        "-r", chosen_route_file,
        "--no-warnings", "true"
    ]

    print(f"\nLaunching SUMO GUI with: {chosen_route_file}\n")
    traci.start(sumo_cmd)

    # --- 4. Run the Simulation Loop ---
    step = 0
    # The loop runs as long as there are vehicles in the simulation
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += 1
    
    print(f"\nSimulation finished after {step} steps.")
    traci.close()


if __name__ == "__main__":
    run_gui_viewer()