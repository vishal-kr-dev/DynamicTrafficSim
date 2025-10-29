import os
import xml.etree.ElementTree as ET

def generate_network():
    """Generate 4-way intersection network"""
    
    # Create nodes file
    nodes = ET.Element('nodes')
    
    # EDITED: Center intersection with traffic_light type
    ET.SubElement(nodes, 'node', id='TL', x='0', y='0', type='traffic_light', tl='TL')
    
    # Edge nodes
    ET.SubElement(nodes, 'node', id='N', x='0', y='200')
    ET.SubElement(nodes, 'node', id='S', x='0', y='-200')
    ET.SubElement(nodes, 'node', id='E', x='200', y='0')
    ET.SubElement(nodes, 'node', id='W', x='-200', y='0')
    
    tree = ET.ElementTree(nodes)
    tree.write('intersection.nod.xml', encoding='utf-8', xml_declaration=True)
    
    # Create edges file
    edges = ET.Element('edges')
    
    # Incoming edges
    ET.SubElement(edges, 'edge', id='N2TL', **{'from': 'N', 'to': 'TL', 'numLanes': '2', 'speed': '13.89'})
    ET.SubElement(edges, 'edge', id='S2TL', **{'from': 'S', 'to': 'TL', 'numLanes': '2', 'speed': '13.89'})
    ET.SubElement(edges, 'edge', id='E2TL', **{'from': 'E', 'to': 'TL', 'numLanes': '2', 'speed': '13.89'})
    ET.SubElement(edges, 'edge', id='W2TL', **{'from': 'W', 'to': 'TL', 'numLanes': '2', 'speed': '13.89'})
    
    # Outgoing edges
    ET.SubElement(edges, 'edge', id='TL2N', **{'from': 'TL', 'to': 'N', 'numLanes': '2', 'speed': '13.89'})
    ET.SubElement(edges, 'edge', id='TL2S', **{'from': 'TL', 'to': 'S', 'numLanes': '2', 'speed': '13.89'})
    ET.SubElement(edges, 'edge', id='TL2E', **{'from': 'TL', 'to': 'E', 'numLanes': '2', 'speed': '13.89'})
    ET.SubElement(edges, 'edge', id='TL2W', **{'from': 'TL', 'to': 'W', 'numLanes': '2', 'speed': '13.89'})
    
    tree = ET.ElementTree(edges)
    tree.write('intersection.edg.xml', encoding='utf-8', xml_declaration=True)
    
    # EDITED: Generate network with traffic light NODE but NO logic (we provide it separately)
    os.system('netconvert --node-files=intersection.nod.xml --edge-files=intersection.edg.xml ' +
              '--output-file=intersection.net.xml ' +
              '--junctions.join=false --tls.guess-signals=true --tls.default-type=static')
    
    # EDITED: Create custom traffic light program with 4 phases (one per direction)
    generate_traffic_light_program()
    
    print("Network files generated successfully")

def generate_traffic_light_program():
    """Generate custom traffic light program - one direction at a time"""
    
    additional = ET.Element('additional')
    
    # EDITED: Use programID='dqn' to avoid conflict with auto-generated '0'
    tl_logic = ET.SubElement(additional, 'tlLogic', id='TL', type='static', programID='dqn', offset='0')
    
    # EDITED: All states must be exactly 20 characters (matching link count)
    # Phase 0: North green (indices 0-4)
    ET.SubElement(tl_logic, 'phase', duration='31', state='GGGggrrrrrrrrrrrrrrr')
    # Phase 1: North yellow
    ET.SubElement(tl_logic, 'phase', duration='3', state='yyyyyrrrrrrrrrrrrrrr')
    
    # Phase 2: East green (indices 5-9)
    ET.SubElement(tl_logic, 'phase', duration='31', state='rrrrrGGGggrrrrrrrrrr')
    # Phase 3: East yellow
    ET.SubElement(tl_logic, 'phase', duration='3', state='rrrrryyyyyrrrrrrrrrr')
    
    # Phase 4: South green (indices 10-14)
    ET.SubElement(tl_logic, 'phase', duration='31', state='rrrrrrrrrrGGGggrrrrr')
    # Phase 5: South yellow
    ET.SubElement(tl_logic, 'phase', duration='3', state='rrrrrrrrrryyyyyrrrrr')
    
    # Phase 6: West green (indices 15-19)
    ET.SubElement(tl_logic, 'phase', duration='31', state='rrrrrrrrrrrrrrrGGGgg')
    # Phase 7: West yellow
    ET.SubElement(tl_logic, 'phase', duration='3', state='rrrrrrrrrrrrrrryyyyy')
    
    tree = ET.ElementTree(additional)
    tree.write('tls_program.add.xml', encoding='utf-8', xml_declaration=True)
    
    print("Traffic light program created (8 phases, 20 links)")

def generate_traffic_routes(num_vehicles=1000):
    """Generate pre-defined traffic routes for training"""
    
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
    
    # Routes (all 12 possible paths through intersection)
    route_defs = [
        ('n_s', 'N2TL TL2S'), ('n_e', 'N2TL TL2E'), ('n_w', 'N2TL TL2W'),
        ('s_n', 'S2TL TL2N'), ('s_e', 'S2TL TL2E'), ('s_w', 'S2TL TL2W'),
        ('e_w', 'E2TL TL2W'), ('e_n', 'E2TL TL2N'), ('e_s', 'E2TL TL2S'),
        ('w_e', 'W2TL TL2E'), ('w_n', 'W2TL TL2N'), ('w_s', 'W2TL TL2S')
    ]
    
    for route_id, edges in route_defs:
        ET.SubElement(routes, 'route', id=route_id, edges=edges)
    
    # EDITED: Generate vehicles with varied departure times and types
    import random
    random.seed(42)
    
    vehicle_types = [('passenger', 0.80), ('bus', 0.10), ('truck', 0.08), ('emergency', 0.02)]
    
    for i in range(num_vehicles):
        depart_time = i * 2 + random.randint(0, 3)  # Varied spacing
        route = random.choice(route_defs)[0]
        
        # Select vehicle type based on probability
        rand_val = random.random()
        cumulative = 0
        veh_type = 'passenger'
        for vtype, prob in vehicle_types:
            cumulative += prob
            if rand_val < cumulative:
                veh_type = vtype
                break
        
        ET.SubElement(routes, 'vehicle', id=f'veh_{i}', type=veh_type, 
                      route=route, depart=str(depart_time))
    
    tree = ET.ElementTree(routes)
    tree.write('traffic.rou.xml', encoding='utf-8', xml_declaration=True)
    
    print(f"Generated {num_vehicles} vehicles in traffic.rou.xml")

def generate_sumo_config():
    """Generate SUMO configuration file"""
    
    config = ET.Element('configuration')
    
    input_elem = ET.SubElement(config, 'input')
    ET.SubElement(input_elem, 'net-file', value='intersection.net.xml')
    ET.SubElement(input_elem, 'route-files', value='traffic.rou.xml')
    # EDITED: Add custom traffic light program
    ET.SubElement(input_elem, 'additional-files', value='tls_program.add.xml')
    
    time_elem = ET.SubElement(config, 'time')
    ET.SubElement(time_elem, 'begin', value='0')
    ET.SubElement(time_elem, 'end', value='3600')
    
    tree = ET.ElementTree(config)
    tree.write('simulation.sumocfg', encoding='utf-8', xml_declaration=True)
    
    print("SUMO configuration file generated")

if __name__ == "__main__":
    print("Generating SUMO simulation files...")
    generate_network()
    generate_traffic_routes(num_vehicles=1000)
    generate_sumo_config()
    print("\nAll files generated successfully!")
    print("Files created: intersection.net.xml, traffic.rou.xml, tls_program.add.xml, simulation.sumocfg")