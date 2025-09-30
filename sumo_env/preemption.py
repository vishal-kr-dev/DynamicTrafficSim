import traci
from shapely.geometry import Point, Polygon

class PreemptionLogic:
    def __init__(self, detection_distance, phases):
        self.detection_distance = detection_distance
        self.phases = phases
        self.intersection_poly = None

    def _get_intersection_polygon(self, junction_id): # <-- ACCEPTS junction_id
        """Gets the polygon shape of the intersection from SUMO."""
        shape = traci.junction.getShape(junction_id) # <-- USES junction_id
        return Polygon(shape)

    def check_for_preemption(self):
        """Checks for nearby ambulances and returns the phase to switch to."""
        # Ensure the polygon has been initialized
        if not self.intersection_poly:
            return None

        for veh_id in traci.vehicle.getIDList():
            if traci.vehicle.getTypeID(veh_id) == "AMBULANCE":
                pos = traci.vehicle.getPosition(veh_id)
                distance = Point(pos).distance(self.intersection_poly)
                
                if distance < self.detection_distance:
                    lane = traci.vehicle.getLaneID(veh_id)
                    # Determine which green phase to activate based on the ambulance's lane
                    if 'N_in' in lane or '_N_' in lane: return self.phases['N_GREEN']
                    if 'E_in' in lane or '_E_' in lane: return self.phases['E_GREEN']
                    if 'S_in' in lane or '_S_' in lane: return self.phases['S_GREEN']
                    if 'W_in' in lane or '_W_' in lane: return self.phases['W_GREEN']
        
        return None # No preemption needed