import pandas as pd
import os
import traci

class TrafficLogger:
    def __init__(self, log_path):
        self.log_path = log_path
        if not os.path.exists(log_path):
            os.makedirs(log_path)

        self.vehicle_data = []
        self.ambulance_data = []
        self.tls_data = []

    def log_step(self, time):
        # Log TLS data
        phase = traci.trafficlight.getPhase("J0")
        self.tls_data.append([time, phase])

        # Log vehicle and ambulance data
        for veh_id in traci.vehicle.getIDList():
            pos = traci.vehicle.getPosition(veh_id)
            speed = traci.vehicle.getSpeed(veh_id)
            
            if traci.vehicle.getTypeID(veh_id) == 'AMBULANCE':
                self.ambulance_data.append([time, veh_id, pos[0], pos[1], speed])
            else:
                self.vehicle_data.append([time, veh_id, pos[0], pos[1], speed])
    
    def save_logs(self):
        pd.DataFrame(self.tls_data, columns=['time', 'phase']).to_csv(os.path.join(self.log_path, 'tls_log.csv'), index=False)
        pd.DataFrame(self.ambulance_data, columns=['time', 'id', 'x', 'y', 'speed']).to_csv(os.path.join(self.log_path, 'ambulance_log.csv'), index=False)
        pd.DataFrame(self.vehicle_data, columns=['time', 'id', 'x', 'y', 'speed']).to_csv(os.path.join(self.log_path, 'vehicles_log.csv'), index=False)
        print(f"Logs saved to '{self.log_path}'")