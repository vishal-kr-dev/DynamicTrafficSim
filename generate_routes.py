import os
import sys
import subprocess
import glob
import re

def generate_route_files(start_episode, total_episodes):
    print(f"Checking for existing route files...")
    
    # Path to the randomTrips.py tool
    random_trips_script = os.path.join(os.environ.get("SUMO_HOME", ""), 'tools', 'randomTrips.py')
    
    routes_dir = "sumo_files/routes"
    if not os.path.exists(routes_dir):
        os.makedirs(routes_dir)
        
    print(f"Generating missing route files from episode {start_episode} to {total_episodes}...")
    for i in range(start_episode, total_episodes):
        route_file_path = os.path.join(routes_dir, f"intersection_episode_{i}.rou.xml")
        
        command = [
            sys.executable, random_trips_script,
            '-n', 'sumo_files/intersection.net.xml',
            '-r', route_file_path,
            '-e', '200',  
            '-p', '8.0',
            '--validate'
        ]
        
        subprocess.run(command, capture_output=True, text=True)
        
        if (i + 1) % 50 == 0:
            print(f"  ...up to episode {i + 1} generated.")
            
    print("Route file generation complete.")

if __name__ == "__main__":
    if 'SUMO_HOME' not in os.environ:
        sys.exit("Please declare environment variable 'SUMO_HOME'")
    
    total_episodes_planned = 500
    
    # --- Find the last generated route file to resume ---
    routes_dir = "sumo_files/routes"
    existing_files = glob.glob(os.path.join(routes_dir, "intersection_episode_*.rou.xml"))
    
    start_from = 0
    if existing_files:
        max_episode = -1
        for f in existing_files:
            match = re.search(r'episode_(\d+)', f)
            if match:
                episode_num = int(match.group(1))
                if episode_num > max_episode:
                    max_episode = episode_num
        start_from = max_episode + 1

    generate_route_files(start_from, total_episodes_planned)