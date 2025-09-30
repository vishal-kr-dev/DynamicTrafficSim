#!/usr/bin/env python3
import os
import subprocess
import sys
import glob
from pathlib import Path
import tempfile

# Setup SUMO_HOME
if 'SUMO_HOME' in os.environ:
    sumo_gui = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui')
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

def create_temp_config(net_file, route_file, additional_file=None):
    """Create temporary SUMO config file"""
    # Convert to absolute paths
    net_file = os.path.abspath(net_file)
    route_file = os.path.abspath(route_file)
    
    config_content = f"""<configuration>
    <input>
        <net-file value="{net_file}"/>
        <route-files value="{route_file}"/>"""
    
    if additional_file and os.path.exists(additional_file):
        additional_file = os.path.abspath(additional_file)
        config_content += f'\n        <additional-files value="{additional_file}"/>'
    
    config_content += """
    </input>
    <time>
        <begin value="0"/>
    </time>
</configuration>"""
    
    # Create temporary config file
    temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.sumocfg', delete=False)
    temp_config.write(config_content)
    temp_config.close()
    
    return temp_config.name

def run_sumo_scenarios(routes_dir, net_file, additional_file=None):
    """Run SUMO-GUI with each random route file"""
    
    # Find all route files
    route_files = glob.glob(os.path.join(routes_dir, "*.rou.xml"))
    
    if not route_files:
        print(f"No route files found in {routes_dir}")
        return
    
    print(f"Found {len(route_files)} route files")
    
    for route_file in sorted(route_files):
        scenario_name = Path(route_file).stem
        print(f"\nRunning scenario: {scenario_name}")
        
        # Create temporary config file
        temp_config = create_temp_config(net_file, route_file, additional_file)
        
        try:
            # Run SUMO-GUI
            subprocess.run([sumo_gui, "-c", temp_config], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {scenario_name}: {e}")
        except KeyboardInterrupt:
            print("\nStopped by user")
            break
        finally:
            # Clean up temp file
            if os.path.exists(temp_config):
                os.unlink(temp_config)
        
        # Ask user if they want to continue
        try:
            continue_choice = input("Continue to next scenario? (y/n): ").lower()
            if continue_choice != 'y':
                break
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    # Configuration
    ROUTES_DIR = "random_routes"
    NET_FILE = "sumo_files/intersection.net.xml"
    ADDITIONAL_FILE = "sumo_files/detectors.add.xml"  
    
    if not os.path.exists(ROUTES_DIR):
        print(f"Routes directory '{ROUTES_DIR}' not found. Run traffic generation script first.")
        sys.exit(1)
    
    run_sumo_scenarios(ROUTES_DIR, NET_FILE, ADDITIONAL_FILE)