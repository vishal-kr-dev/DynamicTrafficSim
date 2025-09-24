# rl_agent/environment.py
import os
import sys
import traci
import subprocess
import numpy as np
from . import config

def discretize_queue(queue_length):
    """Converts a raw queue count into a discrete category."""
    if queue_length == 0: return 0  # Empty
    elif queue_length <= 3: return 1  # Low
    elif queue_length <= 7: return 2  # Medium
    else: return 3  # High

class SumoEnvironment:
    def __init__(self, use_gui=False, delay=0):
        self.use_gui = use_gui
        self.delay = delay
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
            self.sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui' if use_gui else 'sumo')
        else:
            sys.exit("please declare environment variable 'SUMO_HOME'")
            
        self.state_size = 5
        self.action_size = 2
        self.phases = {}
        self.phase_map_names = []
        self.current_phase_index = 0
        self.phase_timer = 0
        self.previous_queues = [0] * 8

    def _start_simulation(self, episode_num):
        """Starts a SUMO simulation for a specific pre-generated route file."""
        route_file = f"sumo_files/routes/intersection_episode_{episode_num}.rou.xml"
        if not os.path.exists(route_file):
            sys.exit(f"Error: Route file not found at {route_file}. Please run generate_routes.py first.")

        sumo_cmd = [self.sumo_binary, 
                    "-c", "sumo_files/intersection.sumocfg",
                    "-r", route_file,
                    "--no-warnings", "true"]
        
        if self.use_gui:
            sumo_cmd.extend(["--start", "--quit-on-end", f"--delay={self.delay}"])
        
        traci.start(sumo_cmd)
        self._build_phase_definitions()

    def _build_phase_definitions(self):
        """Asks SUMO for the traffic light's signal order and builds the PHASES dictionary."""
        controlled_lanes = traci.trafficlight.getControlledLanes("J0")
        num_signals = len(controlled_lanes)
        signal_to_direction = {}
        for i, lane_id in enumerate(controlled_lanes):
            if "edge_north_in" in lane_id: signal_to_direction[i] = "N"
            elif "edge_east_in" in lane_id: signal_to_direction[i] = "E"
            elif "edge_south_in" in lane_id: signal_to_direction[i] = "S"
            elif "edge_west_in" in lane_id: signal_to_direction[i] = "W"
            
        self.phase_map_names = ["North Green", "North Yellow", "East Green", "East Yellow", "South Green", "South Yellow", "West Green", "West Yellow"]
        self.phases = {}
        for dir_char, dir_name in [("N", "North"), ("E", "East"), ("S", "South"), ("W", "West")]:
            green_state, yellow_state = "", ""
            for i in range(num_signals):
                if signal_to_direction.get(i) == dir_char:
                    green_state += "G"
                    yellow_state += "y"
                else:
                    green_state += "r"
                    yellow_state += "r"
            self.phases[f"{dir_name} Green"] = green_state
            self.phases[f"{dir_name} Yellow"] = yellow_state

    def reset(self, episode_num=0):
        """Resets the environment for a new episode."""
        if traci.isLoaded():
            traci.close()
        self._start_simulation(episode_num)
        self.current_phase_index = 0
        self.phase_timer = 0
        traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.phase_map_names[self.current_phase_index]])
        self.previous_queues = self._get_raw_queues()
        return self._get_state()

    def step(self, action):
        """Applies an action and advances the simulation by one step."""
        current_phase_name = self.phase_map_names[self.current_phase_index]
        
        # Logic for green phases
        if "Green" in current_phase_name and self.phase_timer > config.MIN_GREEN_TIME:
            if action == 1 or self.phase_timer > config.MAX_GREEN_TIME:
                self.current_phase_index += 1 # Move to yellow
                self.phase_timer = 0
        # Logic for yellow phases
        elif "Yellow" in current_phase_name and self.phase_timer > config.YELLOW_TIME:
            self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_map_names)
            self.phase_timer = 0
        
        traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.phase_map_names[self.current_phase_index]])
        traci.simulationStep()
        self.phase_timer += 1
        
        current_queues = self._get_raw_queues()
        reward = self._get_shaped_reward(current_queues, action)
        state = self._get_state()
        done = traci.simulation.getMinExpectedNumber() == 0
        self.previous_queues = current_queues
        return state, reward, done
    
    def get_valid_actions(self):
        """Returns a list of valid actions based on the current state."""
        current_phase_name = self.phase_map_names[self.current_phase_index]
        if "Yellow" in current_phase_name: return [0]
        if self.phase_timer < config.MIN_GREEN_TIME: return [0]
        if self.phase_timer > config.MAX_GREEN_TIME: return [1]
        return [0, 1]

    def _get_raw_queues(self):
        """Returns a list of 8 raw queue counts for each detector."""
        return [
            traci.lanearea.getLastStepHaltingNumber("det_N_0"),
            traci.lanearea.getLastStepHaltingNumber("det_N_1"),
            traci.lanearea.getLastStepHaltingNumber("det_E_0"),
            traci.lanearea.getLastStepHaltingNumber("det_E_1"),
            traci.lanearea.getLastStepHaltingNumber("det_S_0"),
            traci.lanearea.getLastStepHaltingNumber("det_S_1"),
            traci.lanearea.getLastStepHaltingNumber("det_W_0"),
            traci.lanearea.getLastStepHaltingNumber("det_W_1")
        ]

    def _get_state(self):
        """Gathers and processes the raw queue data into the final state."""
        raw_queues = self._get_raw_queues()
        # Sum the two lanes for each approach
        north_q = raw_queues[0] + raw_queues[1]
        east_q = raw_queues[2] + raw_queues[3]
        south_q = raw_queues[4] + raw_queues[5]
        west_q = raw_queues[6] + raw_queues[7]
        
        # Discretize the summed counts
        discretized_queues = [discretize_queue(q) for q in [north_q, east_q, south_q, west_q]]
        
        return np.array(discretized_queues + [self.current_phase_index]).reshape(1, self.state_size)

    def _get_shaped_reward(self, current_queues, action):
        """Calculates a more detailed reward signal."""
        queue_reduction = sum(self.previous_queues) - sum(current_queues)
        stability_bonus = 0.1 if action == 0 and self.phase_timer > 5 else 0
        # The main penalty is the total number of cars currently stopped
        return -sum(current_queues) + queue_reduction + stability_bonus

    def close(self):
        """Closes the Traci connection."""
        if traci.isLoaded():
            traci.close()