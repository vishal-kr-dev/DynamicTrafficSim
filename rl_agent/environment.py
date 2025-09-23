# rl_agent/environment.py
import os
import sys
import traci
import subprocess
import numpy as np
from rl_agent import config

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
            
        self.state_size = 5 # [qN, qE, qS, qW, phase_id]
        self.action_size = 2 # 0: CONTINUE, 1: SWITCH
        self.phases = {}
        self.phase_map_names = []
        self.current_phase_index = 0
        self.phase_timer = 0

    def _start_simulation(self):
        # Generate new random traffic for the episode
        # Set to light traffic for faster initial training
        subprocess.call([sys.executable, os.path.join(os.environ['SUMO_HOME'], 'tools', 'randomTrips.py'),
                         '-n', 'sumo_files/intersection.net.xml',
                         '-r', 'sumo_files/intersection.rou.xml',
                         '-e', '600', '-p', '8.0', '--validate'],
                        stdout=sys.stdout, stderr=sys.stderr)

        sumo_cmd = [self.sumo_binary, "-c", "sumo_files/intersection.sumocfg", "--no-warnings", "true"]
        if self.use_gui:
            sumo_cmd.append("--start")
            sumo_cmd.append("--quit-on-end")
            sumo_cmd.append(f"--delay={self.delay}")
        
        traci.start(sumo_cmd)
        self._build_phase_definitions()

    def _build_phase_definitions(self):
        controlled_lanes = traci.trafficlight.getControlledLanes("J0")
        num_signals = len(controlled_lanes)
        signal_to_direction = {}
        for i, lane_id in enumerate(controlled_lanes):
            if "edge_north_in" in lane_id: signal_to_direction[i] = "N"
            elif "edge_east_in" in lane_id: signal_to_direction[i] = "E"
            elif "edge_south_in" in lane_id: signal_to_direction[i] = "S"
            elif "edge_west_in" in lane_id: signal_to_direction[i] = "W"
        
        # This defines the full, predictable N->E->S->W cycle
        self.phase_map_names = ["North Green", "North Yellow", "East Green", "East Yellow", "South Green", "South Yellow", "West Green", "West Yellow"]
        self.phases = {}
        for dir_char, dir_name in [("N", "North"), ("E", "East"), ("S", "South"), ("W", "West")]:
            green_state, yellow_state = "", ""
            for i in range(num_signals):
                if signal_to_direction.get(i) == dir_char:
                    green_state += "G"; yellow_state += "y"
                else:
                    green_state += "r"; yellow_state += "r"
            self.phases[f"{dir_name} Green"] = green_state
            self.phases[f"{dir_name} Yellow"] = yellow_state

    def reset(self):
        if traci.isLoaded():
            traci.close()
        self._start_simulation()
        self.current_phase_index = 0 # Start with the first phase (North Green)
        self.phase_timer = 0
        traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.phase_map_names[self.current_phase_index]])
        return self._get_state()

    def step(self, action):
        # action 0: CONTINUE, action 1: SWITCH
        current_phase_name = self.phase_map_names[self.current_phase_index]
        
        # Agent decides to switch only during a green light and after the minimum time
        if "Green" in current_phase_name and self.phase_timer > config.MIN_GREEN_TIME:
            if action == 1 or self.phase_timer > config.MAX_GREEN_TIME:
                # Switch to the corresponding yellow phase
                self.current_phase_index += 1 
                traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.phase_map_names[self.current_phase_index]])
                self.phase_timer = 0
        
        # Yellow light logic is fixed and automatic
        elif "Yellow" in current_phase_name:
            if self.phase_timer > config.YELLOW_TIME:
                # Move to the next green phase in the cycle
                self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_map_names)
                traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.phase_map_names[self.current_phase_index]])
                self.phase_timer = 0

        traci.simulationStep()
        self.phase_timer += 1
        
        state = self._get_state()
        reward = self._get_reward()
        done = traci.simulation.getMinExpectedNumber() == 0
        
        return state, reward, done

    def _get_state(self):
        queues = [
            traci.lanearea.getLastStepHaltingNumber("det_N_0") + traci.lanearea.getLastStepHaltingNumber("det_N_1"),
            traci.lanearea.getLastStepHaltingNumber("det_E_0") + traci.lanearea.getLastStepHaltingNumber("det_E_1"),
            traci.lanearea.getLastStepHaltingNumber("det_S_0") + traci.lanearea.getLastStepHaltingNumber("det_S_1"),
            traci.lanearea.getLastStepHaltingNumber("det_W_0") + traci.lanearea.getLastStepHaltingNumber("det_W_1")
        ]
        # State: 4 queues, current green phase index (0=N, 2=E, 4=S, 6=W)
        state = np.array(queues + [self.current_phase_index]).reshape(1, self.state_size)
        return state

    def _get_reward(self):
        vehicles = traci.vehicle.getIDList()
        total_wait_time = sum(traci.vehicle.getWaitingTime(v_id) for v_id in vehicles)
        throughput = traci.simulation.getArrivedNumber()
        reward = (throughput * 10) - (total_wait_time * 0.1)
        return reward

    def close(self):
        if traci.isLoaded():
            traci.close()