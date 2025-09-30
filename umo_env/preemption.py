import traci
from shapely.geometry import Point, Polygon

class PreemptionLogic:
    def __init__(self, detection_distance, phases):
        self.detection_distance = detection_distance
        self.phases = phases
        self.intersection_poly = self._get_intersection_polygon()

    def _get_intersection_polygon(self):
        shape = traci.junction.getShape("J0")
        return Polygon(shape)

    def check_for_preemption(self):
        for veh_id in traci.vehicle.getIDList():
            if traci.vehicle.getTypeID(veh_id) == "AMBULANCE":
                pos = traci.vehicle.getPosition(veh_id)
                distance = Point(pos).distance(self.intersection_poly)
                
                if distance < self.detection_distance:
                    lane = traci.vehicle.getLaneID(veh_id)
                    if 'N_in' in lane: return self.phases['N_GREEN']
                    if 'E_in' in lane: return self.phases['E_GREEN']
                    if 'S_in' in lane: return self.phases['S_GREEN']
                    if 'W_in' in lane: return self.phases['W_GREEN']
        return None # No preemption needed