import os
import sys
import traci
import rl_agent.config as config
import visualizer

PHASES = {}

def build_phase_definitions():
    global PHASES
    controlled_lanes = traci.trafficlight.getControlledLanes("J0")
    num_signals = len(controlled_lanes)
    
    signal_to_direction = {}
    for i, lane_id in enumerate(controlled_lanes):
        if "edge_north_in" in lane_id: signal_to_direction[i] = "N"
        elif "edge_east_in" in lane_id: signal_to_direction[i] = "E"
        elif "edge_south_in" in lane_id: signal_to_direction[i] = "S"
        elif "edge_west_in" in lane_id: signal_to_direction[i] = "W"

    for direction_char in ["N", "E", "S", "W"]:
        green_state, yellow_state = "", ""
        for i in range(num_signals):
            if signal_to_direction.get(i) == direction_char:
                green_state += "G"
                yellow_state += "y"
            else:
                green_state += "r"
                yellow_state += "r"
        
        if direction_char == "N": 
            PHASES["North Green"], PHASES["North Yellow"] = green_state, yellow_state
        elif direction_char == "E":
            PHASES["East Green"], PHASES["East Yellow"] = green_state, yellow_state
        elif direction_char == "S":
            PHASES["South Green"], PHASES["South Yellow"] = green_state, yellow_state
        elif direction_char == "W":
            PHASES["West Green"], PHASES["West Yellow"] = green_state, yellow_state

def get_total_wait_times():
    wait_times = { "North": 0.0, "South": 0.0, "East": 0.0, "West": 0.0 }
    
    detector_map = {
        "North": ["det_N_0", "det_N_1"], "South": ["det_S_0", "det_S_1"],
        "East": ["det_E_0", "det_E_1"], "West": ["det_W_0", "det_W_1"]
    }

    for direction, det_list in detector_map.items():
        for det_id in det_list:
            vehicles_in_det = traci.lanearea.getLastStepVehicleIDs(det_id)
            for veh_id in vehicles_in_det:
                wait_times[direction] += traci.vehicle.getWaitingTime(veh_id)
    return wait_times

def run():
    step = 0
    current_phase_str = PHASES["North Green"]
    phase_timer = 0
    calculated_green_time = config.MIN_GREEN_TIME
    
    if config.ENABLE_GUI_DISPLAY:
        visualizer.setup_display()

    traci.trafficlight.setRedYellowGreenState("J0", current_phase_str)

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # --- Gather all data at the start of the step ---
        queues = {
            "North": traci.lanearea.getLastStepHaltingNumber("det_N_0") + traci.lanearea.getLastStepHaltingNumber("det_N_1"),
            "South": traci.lanearea.getLastStepHaltingNumber("det_S_0") + traci.lanearea.getLastStepHaltingNumber("det_S_1"),
            "East": traci.lanearea.getLastStepHaltingNumber("det_E_0") + traci.lanearea.getLastStepHaltingNumber("det_E_1"),
            "West": traci.lanearea.getLastStepHaltingNumber("det_W_0") + traci.lanearea.getLastStepHaltingNumber("det_W_1")
        }
        wait_times = get_total_wait_times() # <-- Added this call
        
        current_phase_name = [name for name, state in PHASES.items() if state == current_phase_str][0]
        
        # Pass all data to the visualizer
        if config.ENABLE_GUI_DISPLAY:
            visualizer.update_display(current_phase_name, phase_timer, queues, wait_times) # <-- Added wait_times here

        # --- Proportional Green Time Logic ---
        if "Green" in current_phase_name:
            if phase_timer > calculated_green_time:
                yellow_phase_name = current_phase_name.replace("Green", "Yellow")
                current_phase_str = PHASES[yellow_phase_name]
                traci.trafficlight.setRedYellowGreenState("J0", current_phase_str)
                phase_timer = 0
        
        elif "Yellow" in current_phase_name:
            if phase_timer > config.YELLOW_TIME:
                if current_phase_name == "North Yellow": next_phase_name = "East Green"
                elif current_phase_name == "East Yellow": next_phase_name = "South Green"
                elif current_phase_name == "South Yellow": next_phase_name = "West Green"
                elif current_phase_name == "West Yellow": next_phase_name = "North Green"
                else: next_phase_name = "North Green"
                
                current_phase_str = PHASES[next_phase_name]
                traci.trafficlight.setRedYellowGreenState("J0", current_phase_str)
                phase_timer = 0
                
                if next_phase_name == "North Green": car_count = queues["North"]
                elif next_phase_name == "East Green": car_count = queues["East"]
                elif next_phase_name == "South Green": car_count = queues["South"]
                else: car_count = queues["West"]

                calculated_green_time = config.MIN_GREEN_TIME + (car_count * config.TIME_PER_CAR)
                calculated_green_time = max(config.MIN_GREEN_TIME, min(calculated_green_time, config.MAX_GREEN_TIME))
        
        phase_timer += 1
        step += 1
    
    traci.close()
    sys.stdout.flush()

if __name__ == "__main__":
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumo_cmd = ["sumo-gui", "-c", "sumo_files/intersection.sumocfg", "--delay", "100"]
    traci.start(sumo_cmd)
    
    build_phase_definitions()
    run()