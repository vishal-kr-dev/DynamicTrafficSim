import json
import os
import numpy as np
import matplotlib.pyplot as plt
from glob import glob

def analyze_training_logs(log_dir='logs'):
    """Analyze training episode logs"""
    
    log_files = sorted(glob(os.path.join(log_dir, 'episode_*.json')))
    
    if not log_files:
        print("No log files found")
        return
    
    episodes_data = []
    
    for log_file in log_files:
        with open(log_file, 'r') as f:
            data = json.load(f)
            episodes_data.append(data['summary'])
    
    # EDITED: Extract metrics for plotting
    avg_waiting_times = [ep['avg_waiting_time'] for ep in episodes_data]
    avg_queue_lengths = [ep['avg_queue_length'] for ep in episodes_data]
    phase_changes = [ep['total_phase_changes'] for ep in episodes_data]
    total_vehicles = [ep['total_vehicles'] for ep in episodes_data]
    
    # Create plots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Waiting time over episodes
    axes[0, 0].plot(avg_waiting_times, 'b-', linewidth=2)
    axes[0, 0].set_xlabel('Episode')
    axes[0, 0].set_ylabel('Avg Waiting Time (s)')
    axes[0, 0].set_title('Average Waiting Time Progress')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Queue length over episodes
    axes[0, 1].plot(avg_queue_lengths, 'r-', linewidth=2)
    axes[0, 1].set_xlabel('Episode')
    axes[0, 1].set_ylabel('Avg Queue Length')
    axes[0, 1].set_title('Average Queue Length Progress')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Phase changes
    axes[1, 0].plot(phase_changes, 'g-', linewidth=2)
    axes[1, 0].set_xlabel('Episode')
    axes[1, 0].set_ylabel('Phase Changes')
    axes[1, 0].set_title('Traffic Light Phase Changes')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Vehicle throughput
    axes[1, 1].plot(total_vehicles, 'm-', linewidth=2)
    axes[1, 1].set_xlabel('Episode')
    axes[1, 1].set_ylabel('Total Vehicles')
    axes[1, 1].set_title('Vehicle Throughput')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('training_analysis.png', dpi=300)
    print("Training analysis saved to training_analysis.png")
    
    # Print statistics
    print("\n=== Training Statistics ===")
    print(f"Total Episodes: {len(episodes_data)}")
    print(f"Avg Waiting Time: {np.mean(avg_waiting_times):.2f}s (±{np.std(avg_waiting_times):.2f})")
    print(f"Avg Queue Length: {np.mean(avg_queue_lengths):.2f} (±{np.std(avg_queue_lengths):.2f})")
    print(f"Avg Phase Changes: {np.mean(phase_changes):.1f}")
    
    # Improvement trend
    if len(avg_waiting_times) >= 20:
        first_20 = np.mean(avg_waiting_times[:20])
        last_20 = np.mean(avg_waiting_times[-20:])
        improvement = ((first_20 - last_20) / first_20) * 100
        print(f"Improvement (first 20 vs last 20): {improvement:.1f}%")

def analyze_vehicle_types(log_dir='logs'):
    """Analyze vehicle type distribution and waiting times"""
    
    log_files = sorted(glob(os.path.join(log_dir, 'episode_*.json')))
    
    vehicle_totals = {'passenger': 0, 'emergency': 0, 'bus': 0, 'truck': 0}
    
    for log_file in log_files:
        with open(log_file, 'r') as f:
            data = json.load(f)
            for vtype, count in data['summary']['vehicles_passed'].items():
                vehicle_totals[vtype] += count
    
    # EDITED: Create pie chart for vehicle distribution
    plt.figure(figsize=(8, 8))
    colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71']
    plt.pie(vehicle_totals.values(), labels=vehicle_totals.keys(), 
            autopct='%1.1f%%', colors=colors, startangle=90)
    plt.title('Vehicle Type Distribution')
    plt.savefig('vehicle_distribution.png', dpi=300)
    print("\nVehicle distribution saved to vehicle_distribution.png")
    
    print("\n=== Vehicle Type Statistics ===")
    total = sum(vehicle_totals.values())
    for vtype, count in vehicle_totals.items():
        print(f"{vtype.capitalize()}: {count} ({count/total*100:.1f}%)")

def analyze_test_results(test_dir='test_logs'):
    """Analyze test results"""
    
    test_files = sorted(glob(os.path.join(test_dir, 'test_*.json')))
    
    if not test_files:
        print("No test files found")
        return
    
    # Use most recent test file
    with open(test_files[-1], 'r') as f:
        test_data = json.load(f)
    
    print("\n=== Test Results Analysis ===")
    
    for episode in test_data:
        summary = episode['summary']
        print(f"\nEpisode {episode['episode'] + 1}:")
        print(f"  Reward: {summary['total_reward']:.1f}")
        print(f"  Avg Waiting: {summary['avg_waiting_time']:.2f}s")
        print(f"  Avg Queue: {summary['avg_queue_length']:.2f}")
        print(f"  Vehicles: {summary['total_vehicles']}")
        print(f"  Phase Changes: {summary['phase_changes']}")
    
    # EDITED: Overall test statistics
    avg_rewards = [ep['summary']['total_reward'] for ep in test_data]
    avg_waiting_times = [ep['summary']['avg_waiting_time'] for ep in test_data]
    
    print("\nOverall Test Performance:")
    print(f"  Avg Reward: {np.mean(avg_rewards):.1f}")
    print(f"  Avg Waiting Time: {np.mean(avg_waiting_times):.2f}s")

def export_csv_summary(log_dir='logs', output_file='training_summary.csv'):
    """Export training summary to CSV for external analysis"""
    
    import csv
    
    log_files = sorted(glob(os.path.join(log_dir, 'episode_*.json')))
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['episode', 'avg_waiting_time', 'avg_queue_length', 
                     'phase_changes', 'total_vehicles', 'passenger', 'emergency', 'bus', 'truck']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, log_file in enumerate(log_files):
            with open(log_file, 'r') as f:
                data = json.load(f)
                summary = data['summary']
                
                row = {
                    'episode': idx + 1,
                    'avg_waiting_time': summary['avg_waiting_time'],
                    'avg_queue_length': summary['avg_queue_length'],
                    'phase_changes': summary['total_phase_changes'],
                    'total_vehicles': summary['total_vehicles'],
                    **summary['vehicles_passed']
                }
                writer.writerow(row)
    
    print(f"\nCSV summary exported to {output_file}")

if __name__ == "__main__":
    print("Analyzing training data...")
    analyze_training_logs()
    analyze_vehicle_types()
    
    if os.path.exists('test_logs'):
        analyze_test_results()
    
    export_csv_summary()
    
    print("\nAnalysis complete!")