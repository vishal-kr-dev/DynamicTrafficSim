import traci

class RewardCalculator:
    def __init__(self, lanes):
        self.lanes = lanes

    def calculate_reward(self):
        total_waiting_time = sum(traci.lane.getWaitingTime(lane) for lane in self.lanes)
        total_queue_length = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in self.lanes)
        
        # Negative reward for congestion
        reward = - (total_waiting_time + total_queue_length)
        return reward