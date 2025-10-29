import xml.etree.ElementTree as ET
import random
import numpy as np

def generate_dynamic_traffic(duration=3600, output_file='traffic_dynamic.rou.xml', 
                             traffic_pattern='rush_hour'):
    """
    Generate dynamic traffic with varying flow rates
    
    Patterns:
    - rush_hour: High traffic 7-9am, 5-7pm
    - random: Random vehicle spawning
    - uniform: Constant flow rate
    """
    
    routes = ET.Element('routes')
    
    # Vehicle types
    ET.SubElement(routes, 'vType', id='passenger', accel='2.6', decel='4.5', sigma='0.5', 
                  length='5', minGap='2.5', maxSpeed='13.89', guiShape='passenger')
    ET.SubElement(routes, 'vType', id='emergency', accel='3.0', decel='5.0', sigma='0.3',
                  length='7', minGap='2.5', maxSpeed='20', guiShape='emergency', color='1,0,0')
    ET.SubElement(routes, 'vType', id='bus', accel='1.8', decel='4.0', sigma='0.5',
                  length='12', minGap='3', maxSpeed='11.11', guiShape='bus')
    ET.SubElement(routes, 'vType', id='truck', accel='2.0', decel='4.0', sigma='0.5',
                  length='10', minGap='3', maxSpeed='11.11', guiShape='truck')
    
    # Route definitions
    route_defs = [
        ('n_s', 'N2TL TL2S'), ('n_e', 'N2TL TL2E'), ('n_w', 'N2TL TL2W'),
        ('s_n', 'S2TL TL2N'), ('s_e', 'S2TL TL2E'), ('s_w', 'S2TL TL2W'),
        ('e_w', 'E2TL TL2W'), ('e_n', 'E2TL TL2N'), ('e_s', 'E2TL TL2S'),
        ('w_e', 'W2TL TL2E'), ('w_n', 'W2TL TL2N'), ('w_s', 'W2TL TL2S')
    ]
    
    for route_id, edges in route_defs:
        ET.SubElement(routes, 'route', id=route_id, edges=edges)
    
    # EDITED: Generate vehicles based on traffic pattern
    vehicle_types = [('passenger', 0.80), ('bus', 0.10), ('truck', 0.08), ('emergency', 0.02)]
    veh_id = 0
    
    if traffic_pattern == 'rush_hour':
        # Simulate rush hour patterns
        for t in range(0, duration, 1):
            hour = (t // 3600) + 7  # Start from 7am
            
            # High flow during rush hours
            if (7 <= hour < 9) or (17 <= hour < 19):
                spawn_prob = 0.4  # 40% chance per second
            else:
                spawn_prob = 0.15  # 15% chance per second
            
            if random.random() < spawn_prob:
                route = random.choice(route_defs)[0]
                veh_type = _select_vehicle_type(vehicle_types)
                
                ET.SubElement(routes, 'vehicle', id=f'dyn_veh_{veh_id}', 
                            type=veh_type, route=route, depart=str(t))
                veh_id += 1
    
    elif traffic_pattern == 'random':
        # Random spawning with Poisson distribution
        for t in range(0, duration, 1):
            num_vehicles = np.random.poisson(0.25)  # Average 0.25 vehicles per second
            
            for _ in range(num_vehicles):
                route = random.choice(route_defs)[0]
                veh_type = _select_vehicle_type(vehicle_types)
                
                ET.SubElement(routes, 'vehicle', id=f'dyn_veh_{veh_id}', 
                            type=veh_type, route=route, depart=str(t))
                veh_id += 1
    
    elif traffic_pattern == 'uniform':
        # Constant flow rate
        for t in range(0, duration, 4):  # One vehicle every 4 seconds
            route = random.choice(route_defs)[0]
            veh_type = _select_vehicle_type(vehicle_types)
            
            ET.SubElement(routes, 'vehicle', id=f'dyn_veh_{veh_id}', 
                        type=veh_type, route=route, depart=str(t))
            veh_id += 1
    
    tree = ET.ElementTree(routes)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    print(f"Generated {veh_id} vehicles with '{traffic_pattern}' pattern")
    print(f"Saved to {output_file}")

def _select_vehicle_type(vehicle_types):
    """Select vehicle type based on probability distribution"""
    rand_val = random.random()
    cumulative = 0
    
    for vtype, prob in vehicle_types:
        cumulative += prob
        if rand_val < cumulative:
            return vtype
    
    return 'passenger'

def generate_incident_scenario(output_file='traffic_incident.rou.xml'):
    """Generate traffic with simulated incident (emergency vehicles)"""
    
    routes = ET.Element('routes')
    
    # Vehicle types
    ET.SubElement(routes, 'vType', id='passenger', accel='2.6', decel='4.5', sigma='0.5', 
                  length='5', minGap='2.5', maxSpeed='13.89', guiShape='passenger')
    ET.SubElement(routes, 'vType', id='emergency', accel='3.0', decel='5.0', sigma='0.3',
                  length='7', minGap='2.5', maxSpeed='20', guiShape='emergency', color='1,0,0')
    
    route_defs = [
        ('n_s', 'N2TL TL2S'), ('e_w', 'E2TL TL2W'), ('s_n', 'S2TL TL2N'), ('w_e', 'W2TL TL2E')
    ]
    
    for route_id, edges in route_defs:
        ET.SubElement(routes, 'route', id=route_id, edges=edges)
    
    veh_id = 0
    
    # Normal traffic for first 300 seconds
    for t in range(0, 300, 3):
        route = random.choice(route_defs)[0]
        ET.SubElement(routes, 'vehicle', id=f'veh_{veh_id}', 
                    type='passenger', route=route, depart=str(t))
        veh_id += 1
    
    # EDITED: Emergency vehicles during incident (300-400 seconds)
    for t in range(300, 400, 20):
        route = random.choice(route_defs)[0]
        ET.SubElement(routes, 'vehicle', id=f'emergency_{veh_id}', 
                    type='emergency', route=route, depart=str(t))
        veh_id += 1
    
    # Normal traffic continues
    for t in range(300, 600, 3):
        route = random.choice(route_defs)[0]
        ET.SubElement(routes, 'vehicle', id=f'veh_{veh_id}', 
                    type='passenger', route=route, depart=str(t))
        veh_id += 1
    
    tree = ET.ElementTree(routes)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    print(f"Generated incident scenario with {veh_id} vehicles")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
    else:
        pattern = 'rush_hour'
    
    print(f"Generating dynamic traffic with pattern: {pattern}")
    
    if pattern == 'incident':
        generate_incident_scenario()
    else:
        generate_dynamic_traffic(duration=3600, traffic_pattern=pattern)
    
    print("\nAvailable patterns: rush_hour, random, uniform, incident")