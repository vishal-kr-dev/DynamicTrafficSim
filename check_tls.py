import os
import sys

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("SUMO_HOME not set")

import traci

# Start simulation
traci.start(['sumo', '-c', 'simulation.sumocfg', '--start'])

# Get traffic light info
tls_id = traci.trafficlight.getIDList()[0]
print(f"Traffic Light ID: {tls_id}")

# EDITED: Switch to custom 'dqn' program
traci.trafficlight.setProgram(tls_id, 'dqn')
print("Switched to 'dqn' program\n")

# Get controlled links
links = traci.trafficlight.getControlledLinks(tls_id)
print(f"\nTotal controlled links: {len(links)}")

# Print each link
for i, link in enumerate(links):
    if link:  # Check if link is not empty
        incoming = link[0][0]
        outgoing = link[0][1]
        print(f"Index {i}: {incoming} -> {outgoing}")

# Get current program
logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
print(f"\nNumber of phases: {len(logic.phases)}")

for i, phase in enumerate(logic.phases):
    print(f"Phase {i}: {phase.state} (duration: {phase.duration}s)")

traci.close()