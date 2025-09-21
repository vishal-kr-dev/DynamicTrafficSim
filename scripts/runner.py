# scripts/runner.py
import os
import sys
import traci
import config

def run():
    step = 0
    current_phase_str = config.PHASES["North Green"]
    phase_timer = 0
    
    traci.trafficlight.setRedYellowGreenState("J0", current_phase_str)

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        # --- GET QUEUE LENGTH (Using the correct module name: traci.lanearea) ---
        north_total = traci.lanearea.getLastStepHaltingNumber("det_N_0") + traci.lanearea.getLastStepHaltingNumber("det_N_1")
        south_total = traci.lanearea.getLastStepHaltingNumber("det_S_0") + traci.lanearea.getLastStepHaltingNumber("det_S_1")
        east_total = traci.lanearea.getLastStepHaltingNumber("det_E_0") + traci.lanearea.getLastStepHaltingNumber("det_E_1")
        west_total = traci.lanearea.getLastStepHaltingNumber("det_W_0") + traci.lanearea.getLastStepHaltingNumber("det_W_1")
        
        # Get the human-readable name of the current phase
        current_phase_name = [name for name, state in config.PHASES.items() if state == current_phase_str][0]

        # State Machine Logic (remains the same as the checkpoint)
        if "Green" in current_phase_name:
            should_switch = False
            if phase_timer > config.MIN_GREEN_TIME:
                if current_phase_name == "North Green" and (east_total > 2 or phase_timer > config.MAX_GREEN_TIME):
                    should_switch, next_phase_str = True, config.PHASES["North Yellow"]
                elif current_phase_name == "East Green" and (south_total > 2 or phase_timer > config.MAX_GREEN_TIME):
                    should_switch, next_phase_str = True, config.PHASES["East Yellow"]
                elif current_phase_name == "South Green" and (west_total > 2 or phase_timer > config.MAX_GREEN_TIME):
                    should_switch, next_phase_str = True, config.PHASES["South Yellow"]
                elif current_phase_name == "West Green" and (north_total > 2 or phase_timer > config.MAX_GREEN_TIME):
                    should_switch, next_phase_str = True, config.PHASES["West Yellow"]
            
            if should_switch:
                current_phase_str = next_phase_str
                traci.trafficlight.setRedYellowGreenState("J0", current_phase_str)
                phase_timer = 0

        elif "Yellow" in current_phase_name:
            if phase_timer > config.YELLOW_TIME:
                if current_phase_name == "North Yellow":
                    next_phase_str = config.PHASES["East Green"]
                elif current_phase_name == "East Yellow":
                    next_phase_str = config.PHASES["South Green"]
                elif current_phase_name == "South Yellow":
                    next_phase_str = config.PHASES["West Green"]
                elif current_phase_name == "West Yellow":
                    next_phase_str = config.PHASES["North Green"]
                
                current_phase_str = next_phase_str
                traci.trafficlight.setRedYellowGreenState("J0", current_phase_str)
                phase_timer = 0
        
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

    sumo_cmd = ["sumo-gui", "-c", "sumo_files/intersection.sumocfg", "--delay", "100"]
    traci.start(sumo_cmd)
    run()