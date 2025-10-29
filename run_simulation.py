#!/usr/bin/env python3
"""
Simulation Runner - Simplified interface for training and testing
"""

import os
import sys
import argparse

def setup_environment():
    """Setup SUMO and generate network files"""
    print("=== Setting up environment ===")
    
    # Check SUMO installation
    if 'SUMO_HOME' not in os.environ:
        print("ERROR: SUMO_HOME environment variable not set")
        print("Please install SUMO and set SUMO_HOME")
        sys.exit(1)
    
    print("✓ SUMO_HOME found")
    
    # Generate network files if not exist
    if not os.path.exists('intersection.net.xml'):
        print("Generating network files...")
        os.system('python sumo_network_gen.py')
    else:
        print("✓ Network files exist")
    
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('test_logs', exist_ok=True)
    print("✓ Directories created")

def train_model(episodes=100):
    """Train DQN model"""
    print(f"\n=== Training DQN Model ({episodes} episodes) ===")
    
    # EDITED: Import and run training
    from traffic_dqn_main import train_agent
    train_agent(episodes=episodes)

def test_model(episodes=5, use_gui=True):
    """Test trained model"""
    print(f"\n=== Testing Model ({episodes} episodes) ===")
    
    if not os.path.exists('models/traffic_dqn.pth'):
        print("ERROR: No trained model found. Please train first.")
        return
    
    from test_model import test_agent
    test_agent('models/traffic_dqn.pth', episodes=episodes, use_gui=use_gui)

def compare_models():
    """Compare DQN with fixed-time control"""
    print("\n=== Comparing DQN vs Fixed-Time ===")
    
    if not os.path.exists('models/traffic_dqn.pth'):
        print("ERROR: No trained model found. Please train first.")
        return
    
    from test_model import compare_with_fixed_time
    compare_with_fixed_time(episodes=3)

def analyze_results():
    """Analyze and visualize results"""
    print("\n=== Analyzing Results ===")
    
    if not os.path.exists('logs') or len(os.listdir('logs')) == 0:
        print("No training logs found")
        return
    
    from data_analyzer import analyze_training_logs, analyze_vehicle_types, export_csv_summary
    analyze_training_logs()
    analyze_vehicle_types()
    export_csv_summary()

def generate_traffic(pattern='rush_hour'):
    """Generate traffic patterns"""
    print(f"\n=== Generating {pattern} Traffic ===")
    
    from dynamic_traffic_gen import generate_dynamic_traffic, generate_incident_scenario
    
    if pattern == 'incident':
        generate_incident_scenario()
    else:
        generate_dynamic_traffic(traffic_pattern=pattern)

def main():
    parser = argparse.ArgumentParser(description='Traffic Light DQN Simulation Runner')
    parser.add_argument('command', choices=['setup', 'train', 'test', 'compare', 'analyze', 'traffic', 'full'],
                       help='Command to run')
    parser.add_argument('--episodes', type=int, default=100, help='Number of episodes (default: 100)')
    parser.add_argument('--no-gui', action='store_true', help='Run without GUI')
    parser.add_argument('--pattern', type=str, default='rush_hour', 
                       choices=['rush_hour', 'random', 'uniform', 'incident'],
                       help='Traffic pattern (default: rush_hour)')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup_environment()
    
    elif args.command == 'train':
        setup_environment()
        train_model(episodes=args.episodes)
    
    elif args.command == 'test':
        test_model(episodes=min(args.episodes, 10), use_gui=not args.no_gui)
    
    elif args.command == 'compare':
        compare_models()
    
    elif args.command == 'analyze':
        analyze_results()
    
    elif args.command == 'traffic':
        generate_traffic(pattern=args.pattern)
    
    elif args.command == 'full':
        # EDITED: Full pipeline - setup, train, test, analyze
        print("=== Running Full Pipeline ===")
        setup_environment()
        train_model(episodes=args.episodes)
        test_model(episodes=5, use_gui=not args.no_gui)
        compare_models()
        analyze_results()
        print("\n✓ Full pipeline complete!")
    
    print("\nDone!")

if __name__ == "__main__":
    main()