import numpy as np
import traci

class TrafficState:
    def __init__(self):
        # This is the corrected list of lanes to monitor.
        # These are the main approach lanes where cars queue up.
        self.lanes = [
            "N_in_0", "E_in_0", "S_in_0", "W_in_0"
        ]
        # The detectors list is no longer needed as we query lanes directly.

    def get_observation(self, current_phase, time_in_phase):
        vehicle_counts = [traci.lane.getLastStepVehicleNumber(lane) for lane in self.lanes]
        waiting_times = [traci.lane.getWaitingTime(lane) for lane in self.lanes]
        
        observation = np.array(vehicle_counts + waiting_times + [current_phase, time_in_phase], dtype=np.float32)
        return observation