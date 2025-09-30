import numpy as np
import traci

class TrafficState:
    def __init__(self):
        self.lanes = [
            ":J1_0_0", ":J1_10_0", ":J1_11_0", ":J1_1_0",
            ":J1_2_0", ":J1_3_0", ":J1_4_0", ":J1_5_0",
            ":J1_6_0", ":J1_7_0", ":J1_8_0", ":J1_9_0"
        ]
        self.detectors = [f"det_{d}" for d in self.lanes]

    def get_observation(self, current_phase, time_in_phase):
        vehicle_counts = [traci.lane.getLastStepVehicleNumber(lane) for lane in self.lanes]
        waiting_times = [traci.lane.getWaitingTime(lane) for lane in self.lanes]
        
        # Normalize and flatten
        observation = np.array(vehicle_counts + waiting_times + [current_phase, time_in_phase], dtype=np.float32)
        return observation