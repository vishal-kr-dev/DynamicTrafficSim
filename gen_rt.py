#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

# Setup SUMO_HOME
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

def generate_random_traffic(net_file, output_dir, num_scenarios=5):
    """Generate random traffic scenarios using SUMO's randomTrips.py"""
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Different randomization parameters for variety
    scenarios = [
        {"period": 5, "end": 3600, "suffix": "heavy"},
        {"period": 10, "end": 3600, "suffix": "medium"},  
        {"period": 20, "end": 3600, "suffix": "light"},
        {"period": 8, "end": 1800, "suffix": "short"},
        {"period": 15, "end": 7200, "suffix": "long"}
    ]
    
    randomtrips_script = os.path.join(os.environ['SUMO_HOME'], 'tools', 'randomTrips.py')
    
    for i, params in enumerate(scenarios[:num_scenarios]):
        route_file = os.path.join(output_dir, f"random_routes_{params['suffix']}.rou.xml")
        
        cmd = [
            "python", randomtrips_script,
            "-n", net_file,
            "-r", route_file,
            "--period", str(params["period"]),
            "--end", str(params["end"]),
            "--seed", str(42 + i),  # Different seed for each scenario
            "--validate"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Generated: {route_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating {route_file}: {e}")

if __name__ == "__main__":
    # Config
    NET_FILE = "sumo_files/intersection.net.xml" 
    OUTPUT_DIR = "random_routes"
    NUM_SCENARIOS = 5
    
    generate_random_traffic(NET_FILE, OUTPUT_DIR, NUM_SCENARIOS)
    print(f"\nGenerated {NUM_SCENARIOS} random traffic scenarios in '{OUTPUT_DIR}' folder")
    
    # print("\nRandomization aspects:")
    # print("- Vehicle departure times (period parameter)")
    # print("- Route selection (random origin-destination pairs)")  
    # print("- Traffic density (period affects vehicle count)")
    # print("- Simulation duration (end time)")
    # print("- Random seed (ensures different patterns)")
    # print("- Vehicle types and speeds (if vtype files provided)")
    # print("- Trip distribution patterns")