#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_traffic_before_green(detector_file, output_csv="analysis/traffic_analysis.csv"):
    """
    Analyze vehicle counts just before each direction gets green light
    Based on your N-E-S-W traffic light sequence (30s green + 3s yellow each)
    """
    
    # Create analysis directory if it doesn't exist
    os.makedirs("analysis", exist_ok=True)
    
    # Parse detector XML output
    try:
        tree = ET.parse(detector_file)
        root = tree.getroot()
    except:
        print(f"Error: Cannot read {detector_file}. Run simulation first.")
        return
    
    # Traffic light cycle timing (from your network)
    cycle_length = 132  # Total: (30+3)*4 = 132 seconds
    phase_times = {
        'N': 0,    # North green starts at 0s
        'E': 33,   # East green starts at 33s  
        'S': 66,   # South green starts at 66s
        'W': 99    # West green starts at 99s
    }
    
    # Extract detector data
    detector_data = {'N': [], 'E': [], 'S': [], 'W': []}
    
    for interval in root.findall('.//interval'):
        time = float(interval.get('begin'))
        detector_id = interval.get('id')
        vehicle_count = int(interval.get('nVehSeen', 0))
        
        # Map detector to direction
        direction = detector_id.split('_')[1]  # det_N -> N
        detector_data[direction].append({
            'time': time,
            'vehicles': vehicle_count
        })
    
    # Find vehicle counts just before green phases
    results = []
    
    for sim_time in range(0, int(max([max([d['time'] for d in data]) for data in detector_data.values()])), cycle_length):
        cycle_start = sim_time
        
        for direction, green_start in phase_times.items():
            check_time = cycle_start + green_start - 1  # 1 second before green
            
            # Find closest detector reading
            direction_data = detector_data[direction]
            closest_reading = min(direction_data, 
                                key=lambda x: abs(x['time'] - check_time),
                                default={'time': check_time, 'vehicles': 0})
            
            results.append({
                'cycle': sim_time // cycle_length,
                'direction': direction,
                'time': check_time,
                'vehicles_waiting': closest_reading['vehicles'],
                'phase_about_to_start': f"{direction} Green"
            })
    
    # Convert to DataFrame and save
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    
    # Print summary
    print(f"\nTraffic Analysis Summary:")
    print(f"{'='*50}")
    for direction in ['N', 'E', 'S', 'W']:
        dir_data = df[df['direction'] == direction]
        avg_waiting = dir_data['vehicles_waiting'].mean()
        max_waiting = dir_data['vehicles_waiting'].max()
        print(f"{direction} Direction: Avg={avg_waiting:.1f}, Max={max_waiting} vehicles before green")
    
    # Plot visualization
    plt.figure(figsize=(12, 8))
    for i, direction in enumerate(['N', 'E', 'S', 'W']):
        dir_data = df[df['direction'] == direction]
        plt.subplot(2, 2, i+1)
        plt.plot(dir_data['cycle'], dir_data['vehicles_waiting'], 'o-')
        plt.title(f'{direction} Direction - Vehicles Before Green')
        plt.xlabel('Cycle Number')
        plt.ylabel('Waiting Vehicles')
        plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('analysis/traffic_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return df

def continuous_traffic_monitoring(detector_file):
    """Monitor traffic continuously for dynamic signal control insights"""
    
    try:
        tree = ET.parse(detector_file)
        root = tree.getroot()
    except:
        print(f"Error: Cannot read {detector_file}")
        return
    
    # Real-time traffic conditions
    traffic_conditions = []
    
    for interval in root.findall('.//interval'):
        time = float(interval.get('begin'))
        detector_id = interval.get('id')
        vehicles = int(interval.get('nVehSeen', 0))
        meanOccupancy = float(interval.get('meanOccupancy', 0))
        speed = float(interval.get('meanSpeed', 0))
        
        direction = detector_id.split('_')[1]
        
        traffic_conditions.append({
            'time': time,
            'direction': direction,
            'vehicles': vehicles,
            'meanOccupancy': meanOccupancy,
            'avg_speed': speed,
            'congestion_level': 'High' if meanOccupancy > 50 else 'Medium' if meanOccupancy > 20 else 'Low'
        })
    
    df = pd.DataFrame(traffic_conditions)
    df.to_csv('analysis/continuous_traffic_monitoring.csv', index=False)
    
    # Print real-time insights
    print(f"\nContinuous Traffic Monitoring:")
    print(f"{'='*50}")
    for direction in ['N', 'E', 'S', 'W']:
        dir_data = df[df['direction'] == direction]
        avg_meanOccupancy = dir_data['meanOccupancy'].mean()
        high_congestion_time = len(dir_data[dir_data['congestion_level'] == 'High'])
        print(f"{direction}: Avg meanOccupancy={avg_meanOccupancy:.1f}%, High Congestion={high_congestion_time} intervals")
    
    return df

if __name__ == "__main__":
    DETECTOR_FILE = "sumo_files/detector_output.xml"  
    
    print("Analyzing traffic patterns for dynamic signal control...")
    
    # Analysis 1: Vehicles waiting before green phases
    df1 = analyze_traffic_before_green(DETECTOR_FILE)
    
    # Analysis 2: Continuous monitoring for adaptive signals
    df2 = continuous_traffic_monitoring(DETECTOR_FILE)
    
    print(f"\nFiles generated:")
    print(f"- analysis/traffic_analysis.csv (pre-green vehicle counts)")
    print(f"- analysis/continuous_traffic_monitoring.csv (all-time conditions)")
    print(f"- analysis/traffic_analysis.png (visualization)")