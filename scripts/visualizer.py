# scripts/visualizer.py
import traci
import rl_agent.config as config

# Define which lanes represent each approach
APPROACH_LANES = {
    "North": "edge_north_in_0",
    "East":  "edge_east_in_0",
    "South": "edge_south_in_0",
    "West":  "edge_west_in_0"
}

# Parameters for the display text
TEXT_SIZE = 15
TEXT_COLOR = (255, 255, 0) # Yellow

def setup_display():
    """Initializes all the on-screen text displays (PoIs)."""
    traci.gui.setZoom("View #0", 1000)
    
    # Create the main status PoI in the corner
    main_poi_id = "info_poi_main"
    traci.poi.add(main_poi_id, x=100, y=900, color=TEXT_COLOR)
    traci.poi.setParameter(main_poi_id, "textSize", TEXT_SIZE * 1.5)
    
    # Create a PoI for each approach, positioned automatically
    for direction, lane_id in APPROACH_LANES.items():
        poi_id = f"info_poi_{direction}"
        shape = traci.lane.getShape(lane_id)
        stop_line_pos = shape[-1] 
        
        offset_x, offset_y = 0, 0
        if direction == "North": offset_x = 10
        elif direction == "South": offset_x = -10
        elif direction == "East": offset_y = -10
        elif direction == "West": offset_y = 10
            
        traci.poi.add(poi_id, x=stop_line_pos[0] + offset_x, y=stop_line_pos[1] + offset_y, color=TEXT_COLOR)
        traci.poi.setParameter(poi_id, "textSize", TEXT_SIZE)


# scripts/visualizer.py# scripts/visualizer.py
import traci
import rl_agent.config as config

# Define which lanes represent each approach
APPROACH_LANES = {
    "North": "edge_north_in_0",
    "East":  "edge_east_in_0",
    "South": "edge_south_in_0",
    "West":  "edge_west_in_0"
}

# Parameters for the display text
TEXT_SIZE = 15
TEXT_COLOR = (255, 255, 0) # Yellow

def setup_display():
    traci.gui.setZoom("View #0", 1000)
    
    # Create the main status PoI in the corner
    main_poi_id = "info_poi_main"
    traci.poi.add(main_poi_id, x=100, y=900, color=TEXT_COLOR)
    traci.poi.setParameter(main_poi_id, "textSize", TEXT_SIZE * 1.5)
    
    # Create a PoI for each approach, positioned automatically
    for direction, lane_id in APPROACH_LANES.items():
        poi_id = f"info_poi_{direction}"
        shape = traci.lane.getShape(lane_id)
        stop_line_pos = shape[-1] 
        
        # --- Increased offset values to move displays further away ---
        offset_x, offset_y = 0, 0
        if direction == "North": 
            offset_x = 5
        elif direction == "South": 
            offset_x = -15
            offset_y = -2
        elif direction == "East": 
            offset_y = -7
        elif direction == "West": 
            offset_y = 2 
            offset_x = -10
            
        traci.poi.add(poi_id, x=stop_line_pos[0] + offset_x, y=stop_line_pos[1] + offset_y, color=TEXT_COLOR)
        traci.poi.setParameter(poi_id, "textSize", TEXT_SIZE)

def update_display(current_phase_name, phase_timer, queues, wait_times):
    """Updates the text in all display boxes with detailed information."""
    
    # 1. Update the main status display
    main_text = (f"Phase: {current_phase_name}\nTimer: {phase_timer}s")
    traci.poi.setParameter("info_poi_main", "text", main_text)
    
    # 2. Update the individual approach displays
    for direction, queue_count in queues.items():
        poi_id = f"info_poi_{direction}"
        light_state = "Red"
        info_text = ""
        
        if direction in current_phase_name:
            if "Green" in current_phase_name:
                light_state = "Green"
                info_text = (f"State: {light_state}\n"
                             f"Timer: {phase_timer}s\n"
                             f"Queue: {queue_count}")
            elif "Yellow" in current_phase_name:
                light_state = "Yellow"
                info_text = (f"State: {light_state}\n"
                             f"Queue: {queue_count}")
        else:
            total_wait_time = wait_times[direction]
            info_text = (f"State: {light_state}\n"
                         f"Wait Time: {total_wait_time:.1f}s\n"
                         f"Queue: {queue_count}")
            
        traci.poi.setParameter(poi_id, "text", info_text)
# ... (setup_display() function and other parts are the same)

def update_display(current_phase_name, phase_timer, queues, wait_times):
    """Updates the text in all display boxes with detailed information."""
    
    # 1. Update the main status display
    main_text = (f"Phase: {current_phase_name}\nTimer: {phase_timer}s")
    traci.poi.setParameter("info_poi_main", "text", main_text)
    
    # 2. Update the individual approach displays
    for direction, queue_count in queues.items():
        poi_id = f"info_poi_{direction}"
        light_state = "Red"
        info_text = ""
        
        if direction in current_phase_name:
            if "Green" in current_phase_name:
                light_state = "Green"
                info_text = (f"State: {light_state}\n"
                             f"Timer: {phase_timer}s\n"
                             f"Queue: {queue_count}")
            elif "Yellow" in current_phase_name:
                light_state = "Yellow"
                info_text = (f"State: {light_state}\n"
                             f"Queue: {queue_count}")
        else:
            # For red lights, show the accumulated wait time
            total_wait_time = wait_times[direction]
            info_text = (f"State: {light_state}\n"
                         f"Wait Time: {total_wait_time:.1f}s\n" # Format to one decimal place
                         f"Queue: {queue_count}")
            
        traci.poi.setParameter(poi_id, "text", info_text)