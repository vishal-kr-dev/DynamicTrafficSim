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
    def __init__(self, config, use_gui=False):
        super(SumoEnv, self).__init__()
        self.config = config
        self.use_gui = use_gui
        self.is_test = not use_gui # A simple flag to differentiate train/test runs

        # State and Action Space
        # Observation: 8 lanes (counts), 8 lanes (wait times), 1 (current phase), 1 (time in phase) = 18
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(18,), dtype=np.float32)
        self.action_space = spaces.Discrete(2) # 0: Keep phase, 1: Change phase

        # SUMO simulation parameters
        self.sim_end = config['sumo']['simulation_end']
        self.min_green = config['sumo']['min_green_time']
        self.max_green = config['sumo']['max_green_time']
        self.yellow_time = config['sumo']['yellow_time']
        self.route_folder = config['sumo']['route_folder']
        
        self.phases = {
            0: "GrGrGrGr", # N-S Green
            1: "yryryryr", # N-S Yellow
            2: "rGrGrGrG", # E-W Green
            3: "ryryryry"  # E-W Yellow
        }
        self.phase_map = {'N_GREEN': 0, 'E_GREEN': 2, 'S_GREEN': 0, 'W_GREEN': 2}
        
        # Modules
        self.traffic_state = TrafficState()
        self.reward_calc = RewardCalculator(self.traffic_state.lanes)
        self.preemption = PreemptionLogic(config['preemption']['detection_distance'], self.phase_map)
        self.logger = TrafficLogger(config['paths']['log_folder']) if self.is_test else None

        self.current_step = 0
        self.current_phase = 0
        self.time_in_phase = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        close_simulation()
        
        prefix = 'test' if self.is_test else 'train'
        num_routes = self.config['routes']['num_test_routes'] if self.is_test else self.config['routes']['num_train_routes']
        route_file = os.path.join(self.route_folder, f"{prefix}_{random.randint(0, num_routes - 1)}.rou.xml")
        
        start_simulation(self.config, route_file, self.use_gui)
        
        self.current_step = 0
        self.current_phase = 0
        self.time_in_phase = 0
        traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.current_phase])

        return self.traffic_state.get_observation(self.current_phase, self.time_in_phase), {}

    def step(self, action):
        preemption_phase = self.preemption.check_for_preemption()

        if preemption_phase is not None:
            # Emergency vehicle detected, override agent's action
            if self.current_phase != preemption_phase:
                self._set_phase(preemption_phase)
        else:
            # Normal DQN control
            is_green_phase = self.current_phase in [0, 2]
            
            # Action logic: 1=Change, 0=Stay
            if is_green_phase and self.time_in_phase > self.min_green and action == 1:
                self._transition_to_yellow()
            elif is_green_phase and self.time_in_phase > self.max_green:
                self._transition_to_yellow()
        
        # Advance simulation
        traci.simulationStep()
        self.current_step += 1
        self.time_in_phase += 1

        # Handle yellow phase transitions
        if self.current_phase in [1, 3] and self.time_in_phase >= self.yellow_time:
            self._transition_to_green()
            
        # Get results
        observation = self.traffic_state.get_observation(self.current_phase, self.time_in_phase)
        reward = self.reward_calc.calculate_reward()
        terminated = self.current_step >= self.sim_end
        
        if self.is_test and self.logger:
            self.logger.log_step(self.current_step)

        return observation, reward, terminated, False, {}

    def _set_phase(self, new_phase):
        if self.current_phase != new_phase:
            self.current_phase = new_phase
            traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.current_phase])
            self.time_in_phase = 0

    def _transition_to_yellow(self):
        self.current_phase += 1 # Assumes Green phases are even, Yellows are odd
        traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.current_phase])
        self.time_in_phase = 0

    def _transition_to_green(self):
        self.current_phase = (self.current_phase + 1) % len(self.phases)
        traci.trafficlight.setRedYellowGreenState("J0", self.phases[self.current_phase])
        self.time_in_phase = 0

    def close(self):
        if self.is_test and self.logger:
            self.logger.save_logs()
        close_simulation()