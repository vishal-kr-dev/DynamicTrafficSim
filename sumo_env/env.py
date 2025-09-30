import gymnasium as gym
from gymnasium import spaces
import numpy as np
import os
import random
import traci

from utils.sumo_runner import start_simulation, close_simulation
from .traffic_state import TrafficState
from .reward import RewardCalculator
from .preemption import PreemptionLogic
from utils.logger import TrafficLogger

class SumoEnv(gym.Env):
    def __init__(self, config, use_gui=False, is_test=False):
        super(SumoEnv, self).__init__()
        # ... (the rest of your __init__ method is the same as before) ...
        self.config = config
        self.use_gui = use_gui
        self.is_test = is_test # A simple flag to differentiate train/test runs

        # SUMO simulation parameters
        self.junction_id = config['sumo']['junction_id']
        self.sim_end = config['sumo']['simulation_end']
        self.min_green = config['sumo']['min_green_time']
        self.max_green = config['sumo']['max_green_time']
        self.yellow_time = config['sumo']['yellow_time']
        self.route_folder = config['sumo']['route_folder']
        
        # Define phases BEFORE they are used by other modules
        self.phases = {
            0: "GGgrrrrrrrrrrr", 1: "yyyrrrrrrrrrrr", 2: "rrrGGgrrrrrrrr", 
            3: "rrryyyrrrrrrrr", 4: "rrrrrrGGgrrrrr", 5: "rrrrrryyyrrrrr",
            6: "rrrrrrrrrGGgrr", 7: "rrrrrrrrryyyrr"
        }
        self.phase_map = {'N_GREEN': 0, 'E_GREEN': 2, 'S_GREEN': 4, 'W_GREEN': 6}

        # Modules
        self.traffic_state = TrafficState()
        self.reward_calc = RewardCalculator(self.traffic_state.lanes)
        self.preemption = PreemptionLogic(config['preemption']['detection_distance'], self.phase_map)
        self.logger = TrafficLogger(config['paths']['log_folder']) if self.is_test else None

        # State and Action Space (Calculated Dynamically)
        num_lanes = len(self.traffic_state.lanes)
        obs_space_size = (num_lanes * 2) + 2
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_space_size,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)

        self.current_step = 0
        self.current_phase = 0
        self.time_in_phase = 0


    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        close_simulation()
        
        prefix = 'test' if self.is_test else 'train'
        num_routes = self.config['routes']['num_test_routes'] if self.is_test else self.config['routes']['num_train_routes']
        route_file = os.path.join(self.route_folder, f"{prefix}_{random.randint(0, num_routes - 1)}.rou.xml")
        
        # --- NEW DEBUG PRINT ---
        print(f"\n[DEBUG] Loading new episode with route file: {os.path.basename(route_file)}")
        
        start_simulation(self.config, route_file, self.use_gui)
        self.preemption.intersection_poly = self.preemption._get_intersection_polygon(self.junction_id)

        self.current_step = 0
        self.current_phase = 0
        self.time_in_phase = 0
        traci.trafficlight.setRedYellowGreenState(self.junction_id, self.phases[self.current_phase])

        return self.traffic_state.get_observation(self.current_phase, self.time_in_phase), {}

    def step(self, action):
        # --- NEW DEBUG PRINT ---
        if self.current_step % 100 == 0: # Print every 100 steps to avoid spam
             print(f"[DEBUG] Step: {self.current_step}, Action: {action}")
        
        # ... (the rest of your step method is the same as before) ...
        preemption_phase = self.preemption.check_for_preemption()

        if preemption_phase is not None:
            if self.current_phase != preemption_phase:
                self._set_phase(preemption_phase)
        else:
            is_green_phase = self.current_phase in [0, 2, 4, 6]
            if is_green_phase and self.time_in_phase > self.min_green and action == 1:
                self._transition_to_yellow()
            elif is_green_phase and self.time_in_phase > self.max_green:
                self._transition_to_yellow()
        
        traci.simulationStep()
        self.current_step += 1
        self.time_in_phase += 1

        if self.current_phase in [1, 3, 5, 7] and self.time_in_phase >= self.yellow_time:
            self._transition_to_green()
            
        observation = self.traffic_state.get_observation(self.current_phase, self.time_in_phase)
        reward = self.reward_calc.calculate_reward()
        terminated = self.current_step >= self.sim_end
        
        if self.is_test and self.logger:
            self.logger.log_step(self.current_step)

        return observation, reward, terminated, False, {}

    # ... (the rest of your file is the same) ...
    def _set_phase(self, new_phase):
        if self.current_phase != new_phase:
            self.current_phase = new_phase
            traci.trafficlight.setRedYellowGreenState(self.junction_id, self.phases[self.current_phase])
            self.time_in_phase = 0

    def _transition_to_yellow(self):
        self.current_phase += 1
        traci.trafficlight.setRedYellowGreenState(self.junction_id, self.phases[self.current_phase])
        self.time_in_phase = 0

    def _transition_to_green(self):
        self.current_phase = (self.current_phase + 1) % len(self.phases)
        traci.trafficlight.setRedYellowGreenState(self.junction_id, self.phases[self.current_phase])
        self.time_in_phase = 0

    def close(self):
        if self.is_test and self.logger:
            self.logger.save_logs()
        close_simulation()