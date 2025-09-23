import os
import sys
import traci
import subprocess
import numpy as np

class SumoEnvironment:
    def __init__(self, use_gui=False, delay=100):
        self.use_gui = use_gui
        self.delay = delay
        if self.use_gui:
            self.sumo_binary = os.environ.get("SUMO_HOME", "c:/sumo") + "/bin/sumo-gui"
        else:
            self.sumo_binary = os.environ.get("SUMO_HOME", "c:/sumo") + "/bin/sumo"
            
        self.state_size = 5 # [qN, qE, qS, qW, phase, timer] it was 6 before 
        self.action_size = 2 # 0: CONTINUE, 1: SWITCH

    def _start_simulation(self):
        # Generate a new random route file for each episode
        subprocess.call(['python', os.environ.get("SUMO_HOME") + '/tools/randomTrips.py',
                         '-n', 'sumo_files/intersection.net.xml',
                         '-r', 'sumo_files/intersection.rou.xml',
                         '-e', '600', '-p', '8.0', '--validate'],
                        stdout=sys.stdout, stderr=sys.stderr)
        # it was 3.0 -> 8.0

        sumo_cmd = [self.sumo_binary, "-c", "sumo_files/intersection.sumocfg"]
        if self.use_gui:
            sumo_cmd.append(f"--delay={self.delay}")
        
        traci.start(sumo_cmd)
        self.phase_timer = 0
        self.current_phase = 0 # 0:N, 1:E, 2:S, 3:W

    def reset(self):
        if traci.isLoaded():
            traci.close()
        self._start_simulation()
        return self._get_state()

    def step(self, action):
        # Action: 0 for CONTINUE, 1 for SWITCH
        if action == 1:
            self.current_phase = (self.current_phase + 1) % 4
            self.phase_timer = 0
        
        # In a real system, you'd have yellow lights. We simplify here.
        phase_map = [
            "GGggrrrrGGggrrrr", # North-South Green
            "rrrrGGggrrrrGGgg"  # East-West Green
        ]
        # This simplified mapping assumes N/S and E/W are paired.
        # It needs to be updated to match your single-phase logic from before.
        # For now, let's keep it simple.
        # We need to map our 4-phase logic (0:N, 1:E, 2:S, 3:W) here.
        # This part will need refinement.
        
        # Let's placeholder this with the knowledge we need to fix it later.
        # A simple state change for now.
        
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
        state = np.array(queues + [self.current_phase, self.phase_timer]).reshape(1, self.state_size)
        return state


    # def _get_reward(self):
    #     # Reward is the negative of total waiting time
    #     vehicles = traci.vehicle.getIDList()
    #     total_wait_time = sum(traci.vehicle.getWaitingTime(v_id) for v_id in vehicles)
    #     return -total_wait_time


    def _get_reward(self):
        # Get the total waiting time (this is our penalty)
        vehicles = traci.vehicle.getIDList()
        total_wait_time = sum(traci.vehicle.getWaitingTime(v_id) for v_id in vehicles)
        
        # Get the number of cars that passed the intersection in the last step (this is our reward)
        # traci.simulation.getArrivedNumber() counts vehicles that finished their trip
        throughput = traci.simulation.getArrivedNumber()
        
        # Combine the penalty and the reward
        # We give a large positive reward for throughput and a smaller penalty for waiting time
        reward = (throughput * 10) - (total_wait_time * 0.1)
        
        return reward

    def close(self):
        traci.close()