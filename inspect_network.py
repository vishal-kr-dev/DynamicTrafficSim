import xml.etree.ElementTree as ET
import argparse
from collections import defaultdict

def inspect_net_file(net_file_path):
    """
    Parses a SUMO .net.xml file to extract information about traffic-controlled
    junctions, their incoming lanes, and their traffic light phase definitions.
    """
    try:
        tree = ET.parse(net_file_path)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: The file '{net_file_path}' was not found.")
        return
    except ET.ParseError:
        print(f"Error: The file '{net_file_path}' is not a valid XML file.")
        return

    # Find all junctions that are controlled by a traffic light
    traffic_light_junctions = root.findall(".//junction[@type='traffic_light']")
    
    if not traffic_light_junctions:
        print("No traffic light controlled junctions found in this file.")
        return

    print(f"Found {len(traffic_light_junctions)} traffic light controlled junction(s):\n")

    for junction in traffic_light_junctions:
        junction_id = junction.get('id')
        print("="*40)
        print(f"✅ Junction ID: {junction_id}")
        print("="*40)

        # --- Find Incoming Lanes for this junction ---
        incoming_lanes = set()
        # Connections are defined by the 'tl' (traffic light) attribute
        connections = root.findall(f".//connection[@tl='{junction_id}']")
        for conn in connections:
            # The 'via' attribute specifies the lane ID of the connection
            lane_id = conn.get('via')
            if lane_id:
                incoming_lanes.add(lane_id)
        
        if incoming_lanes:
            print("\n🚗 Incoming Lane IDs (for sumo_env/traffic_state.py):")
            # Sort for consistent output
            for lane in sorted(list(incoming_lanes)):
                print(f"  - \"{lane}\"")
        else:
            print("\nNo incoming lanes with traffic light connections found for this junction.")

        # --- Find Traffic Light Phases for this junction ---
        tl_logic = root.find(f".//tlLogic[@id='{junction_id}']")
        if tl_logic is not None:
            print("\n🚦 Traffic Light Phases (for sumo_env/env.py):")
            phases = tl_logic.findall('phase')
            for i, phase in enumerate(phases):
                duration = phase.get('duration')
                state = phase.get('state')
                print(f"  - Phase {i}: duration=\"{duration}\", state=\"{state}\"")
        else:
            print("\nNo <tlLogic> definition found for this junction.")
        
        print("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect a SUMO .net.xml file for junction, lane, and traffic light info.")
    parser.add_argument("net_file", help="Path to the .net.xml file you want to inspect.")
    args = parser.parse_args()
    
    inspect_net_file(args.net_file)