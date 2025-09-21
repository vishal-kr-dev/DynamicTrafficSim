# scripts/runner.py
import os
import sys
import traci
import config
import visualizer

def run():
    step = 0
    current_phase_str = config.PHASES["North Green"]
    phase_timer = 0
    calculated_green_time = config.MIN_GREEN_TIME
    
    if config.ENABLE_GUI_DISPLAY:
        visualizer.setup_display()

    traci.trafficlight.setRedYellowGreenState("J0", current_phase_str)

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # --- Get data ONCE at the start of the step ---
        queues = {
            "North": traci.lanearea.getLastStepHaltingNumber("det_N_0") + traci.lanearea.getLastStepHaltingNumber("det_N_1"),
            "South": traci.lanearea.getLastStepHaltingNumber("det_S_0") + traci.lanearea.getLastStepHaltingNumber("det_S_1"),
            "East": traci.lanearea.getLastStepHaltingNumber("det_E_0") + traci.lanearea.getLastStepHaltingNumber("det_E_1"),
            "West": traci.lanearea.getLastStepHaltingNumber("det_W_0") + traci.lanearea.getLastStepHaltingNumber("det_W_1")
        }
        
        current_phase_name = [name for name, state in config.PHASES.items() if state == current_phase_str][0]
        
        # Pass the collected data to the visualizer
        if config.ENABLE_GUI_DISPLAY:
            visualizer.update_display(current_phase_name, phase_timer, queues)

        # --- Proportional Green Time Logic ---
        if "Green" in current_phase_name:
            if phase_timer > calculated_green_time:
                yellow_phase_name = current_phase_name.replace("Green", "Yellow")
                current_phase_str = config.PHASES[yellow_phase_name]
                traci.trafficlight.setRedYellowGreenState("J0", current_phase_str)
                phase_timer = 0
        
        elif "Yellow" in current_phase_name:
            if phase_timer > config.YELLOW_TIME:
                if current_phase_name == "North Yellow": next_phase_name = "East Green"
                elif current_phase_name == "East Yellow": next_phase_name = "South Green"
                elif current_phase_name == "South Yellow": next_phase_name = "West Green"
                elif current_phase_name == "West Yellow": next_phase_name = "North Green"
                else: next_phase_name = "North Green"
                
                current_phase_str = config.PHASES[next_phase_name]
                traci.trafficlight.setRedYellowGreenState("J0", current_phase_str)
                phase_timer = 0
                
                # --- Calculate duration using the already-collected data ---
                if next_phase_name == "North Green":
                    car_count = queues["North"]
                elif next_phase_name == "East Green":
                    car_count = queues["East"]
                elif next_phase_name == "South Green":
                    car_count = queues["South"]
                else: # West Green
                    car_count = queues["West"]

                calculated_green_time = config.MIN_GREEN_TIME + (car_count * config.TIME_PER_CAR)
                calculated_green_time = max(config.MIN_GREEN_TIME, min(calculated_green_time, config.MAX_GREEN_TIME))
        
        phase_timer += 1
        step += 1
    
    traci.close()
    sys.stdout.flush()

# Boilerplate setup code (remains the same)
if __name__ == "__main__":
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumo_cmd = ["sumo-gui", "-c", "sumo_files/intersection.sumocfg", "--delay", "10"]
    traci.start(sumo_cmd)
    run()