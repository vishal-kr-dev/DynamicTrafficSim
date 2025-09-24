# rl_agent/environment.py
import os
import sys
import traci
import subprocess
import numpy as np
import shutil
from . import config

def discretize_queue(queue_length):
    if queue_length == 0: return 0
    elif queue_length <= 3: return 1
    elif queue_length <= 7: return 2
    else: return 3

class SumoEnvironment:
    def __init__(self, use_gui=False, delay=0, worker_id=0):
        self.use_gui = use_gui; self.delay = delay; self.worker_id = worker_id

        self.main_temp_dir = "temp"
        self.temp_dir = os.path.join(self.main_temp_dir, f"worker_{self.worker_id}")
        
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools'); sys.path.append(tools)
            self.sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui' if use_gui else 'sumo')
        else: sys.exit("please declare environment variable 'SUMO_HOME'")
        self.state_size = 5; self.action_size = 2; self.phases = {}; self.phase_map_names = []
        self.current_phase_index = 0; self.phase_timer = 0; self.previous_queues = [0] * 8

    def _start_simulation(self):
        if not os.path.exists(self.main_temp_dir):
            os.makedirs(self.main_temp_dir)
            
        # Create a temporary workspace for this worker
        if os.path.exists(self.temp_dir): shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir)
    
        net_file = os.path.join(self.temp_dir, "intersection.net.xml"); rou_file = os.path.join(self.temp_dir, "intersection.rou.xml")
        add_file = os.path.join(self.temp_dir, "intersection.add.xml"); cfg_file = os.path.join(self.temp_dir, "intersection.sumocfg")
        shutil.copy("sumo_files/intersection.net.xml", net_file); shutil.copy("sumo_files/intersection.add.xml", add_file)
        subprocess.run([sys.executable, os.path.join(os.environ['SUMO_HOME'], 'tools', 'randomTrips.py'),
                         '-n', net_file, '-r', rou_file, '-e', '600', '-p', '8.0', '--validate'], capture_output=True, text=True)
        with open(cfg_file, "w") as f:
            f.write(f"""<configuration><input><net-file value="{os.path.basename(net_file)}"/><route-files value="{os.path.basename(rou_file)}"/><additional-files value="{os.path.basename(add_file)}"/></input><time><begin value="0"/></time></configuration>""")
        sumo_cmd = [self.sumo_binary, "-c", cfg_file, "--no-warnings", "true"]
        if self.use_gui: sumo_cmd.extend([f"--start", f"--quit-on-end", f"--delay={self.delay}"])
        traci.start(sumo_cmd); self._build_phase_definitions()

    def _build_phase_definitions(self):
        controlled_lanes = traci.trafficlight.getControlledLanes("J0"); num_signals = len(controlled_lanes); signal_to_direction = {}
        for i, lane_id in enumerate(controlled_lanes):
            if "edge_north_in" in lane_id: signal_to_direction[i] = "N"
            elif "edge_east_in" in lane_id: signal_to_direction[i] = "E"
            elif "edge_south_in" in lane_id: signal_to_direction[i] = "S"
            elif "edge_west_in" in lane_id: signal_to_direction[i] = "W"
        self.phase_map_names = ["North Green", "North Yellow", "East Green", "East Yellow", "South Green", "South Yellow", "West Green", "West Yellow"]
        self.phases = {}
        for dir_char, dir_name in [("N", "North"), ("E", "East"), ("S", "South"), ("W", "West")]:
            green_state, yellow_state = "", "";
            for i in range(num_signals):
                if signal_to_direction.get(i) == dir_char: green_state += "G"; yellow_state += "y"
                else: green_state += "r"; yellow_state += "r"
            self.phases[f"{dir_name} Green"] = green_state; self.phases[f"{dir_name} Yellow"] = yellow_state

    def reset(self):
        if traci.isLoaded(): traci.close()
        self._start_simulation(); self.current_phase_index = 0; self.phase_timer = 0
        traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.phase_map_names[self.current_phase_index]])
        self.previous_queues = self._get_raw_queues(); return self._get_state()

    def step(self, action):
        current_phase_name = self.phase_map_names[self.current_phase_index]
        if "Green" in current_phase_name and self.phase_timer > config.MIN_GREEN_TIME:
            if action == 1 or self.phase_timer > config.MAX_GREEN_TIME: self.current_phase_index += 1; self.phase_timer = 0
        elif "Yellow" in current_phase_name and self.phase_timer > config.YELLOW_TIME:
            self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_map_names); self.phase_timer = 0
        traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.phase_map_names[self.current_phase_index]])
        traci.simulationStep(); self.phase_timer += 1
        current_queues = self._get_raw_queues(); reward = self._get_shaped_reward(current_queues, action)
        state = self._get_state(); done = traci.simulation.getMinExpectedNumber() == 0
        self.previous_queues = current_queues
        return state, reward, done
    
    def get_valid_actions(self):
        current_phase_name = self.phase_map_names[self.current_phase_index]
        if "Yellow" in current_phase_name or self.phase_timer < config.MIN_GREEN_TIME: return [0]
        if self.phase_timer > config.MAX_GREEN_TIME: return [1]
        return [0, 1]

    def _get_raw_queues(self):
        return [traci.lanearea.getLastStepHaltingNumber(f"det_{d}_{i}") for d in "NESW" for i in range(2)]

    def _get_state(self):
        raw_queues = self._get_raw_queues()
        north_q = raw_queues[0] + raw_queues[1]; east_q = raw_queues[2] + raw_queues[3]
        south_q = raw_queues[4] + raw_queues[5]; west_q = raw_queues[6] + raw_queues[7]
        discretized_queues = [discretize_queue(q) for q in [north_q, east_q, south_q, west_q]]
        return np.array(discretized_queues + [self.current_phase_index]).reshape(1, self.state_size)

    def _get_shaped_reward(self, current_queues, action):
        queue_reduction = sum(self.previous_queues) - sum(current_queues)
        stability_bonus = 0.1 if action == 0 and self.phase_timer > 5 else 0
        return -sum(current_queues) + queue_reduction + stability_bonus

    def close(self):
        if traci.isLoaded(): traci.close()
        if os.path.exists(self.temp_dir): shutil.rmtree(self.temp_dir)