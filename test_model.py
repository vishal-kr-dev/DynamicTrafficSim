import os
import sys
import numpy as np
import torch
import json
from datetime import datetime

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci

# Import from main training script
from traffic_dqn_main import DQNAgent, TrafficEnvironment

def test_agent(model_path, episodes=5, use_gui=True):
    """Test trained DQN agent with detailed logging"""
    
    env = TrafficEnvironment('intersection.net.xml', 'traffic.rou.xml', use_gui=use_gui)
    # EDITED: 4 actions (N, E, S, W)
    agent = DQNAgent(state_size=6, action_size=4)
    
    # Load trained model
    agent.load(model_path)
    agent.epsilon = 0  # No exploration during testing
    
    test_results = []
    
    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        steps = 0
        
        episode_metrics = {
            'episode': episode,
            'actions_taken': [],
            'rewards': []
        }
        
        while True:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            
            episode_metrics['actions_taken'].append(int(action))
            episode_metrics['rewards'].append(float(reward))
            
            state = next_state
            total_reward += reward
            steps += 1
            
            if done:
                break
        
        # EDITED: Calculate and log test metrics
        avg_waiting = np.mean(env.episode_data['waiting_times'])
        avg_queue = np.mean(env.episode_data['queue_lengths'])
        
        episode_metrics['summary'] = {
            'total_reward': float(total_reward),
            'steps': steps,
            'avg_waiting_time': float(avg_waiting),
            'avg_queue_length': float(avg_queue),
            'vehicles_passed': env.episode_data['vehicles_passed'],
            'total_vehicles': env.episode_data['total_vehicles'],
            'phase_changes': len(env.episode_data['phase_changes'])
        }
        
        test_results.append(episode_metrics)
        
        print(f"\nTest Episode {episode+1}/{episodes}")
        print(f"  Total Reward: {total_reward:.1f}")
        print(f"  Avg Waiting Time: {avg_waiting:.2f}s")
        print(f"  Avg Queue Length: {avg_queue:.2f}")
        print(f"  Vehicles Passed: {env.episode_data['total_vehicles']}")
    
    # Save test results
    os.makedirs('test_logs', exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'test_logs/test_{timestamp}.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    env.close()
    print(f"\nTest complete. Results saved to test_logs/test_{timestamp}.json")

def compare_with_fixed_time(episodes=3):
    """Compare DQN agent with fixed-time control"""
    
    print("\n=== Testing Fixed-Time Control ===")
    env = TrafficEnvironment('intersection.net.xml', 'traffic.rou.xml', use_gui=False)
    
    fixed_results = []
    
    for episode in range(episodes):
        state = env.reset()
        steps = 0
        total_reward = 0
        
        # EDITED: Fixed 30-second cycles for 4 directions (N, E, S, W)
        phase_duration = 30
        current_action = 0
        
        while True:
            if steps % phase_duration == 0:
                current_action = (current_action + 1) % 4  # Cycle through 4 directions
            
            next_state, reward, done = env.step(current_action)
            total_reward += reward
            steps += 1
            
            if done:
                break
        
        avg_waiting = np.mean(env.episode_data['waiting_times'])
        fixed_results.append({
            'reward': total_reward,
            'avg_waiting': avg_waiting,
            'vehicles': env.episode_data['total_vehicles']
        })
    
    env.close()
    
    # Test DQN
    print("\n=== Testing DQN Control ===")
    env = TrafficEnvironment('intersection.net.xml', 'traffic.rou.xml', use_gui=False)
    # EDITED: 4 actions (N, E, S, W)
    agent = DQNAgent(state_size=6, action_size=4)
    agent.load('models/traffic_dqn.pth')
    agent.epsilon = 0
    
    dqn_results = []
    
    for episode in range(episodes):
        state = env.reset()
        steps = 0
        total_reward = 0
        
        while True:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            state = next_state
            total_reward += reward
            steps += 1
            
            if done:
                break
        
        avg_waiting = np.mean(env.episode_data['waiting_times'])
        dqn_results.append({
            'reward': total_reward,
            'avg_waiting': avg_waiting,
            'vehicles': env.episode_data['total_vehicles']
        })
    
    env.close()
    
    # EDITED: Print comparison results
    print("\n=== Comparison Results ===")
    fixed_avg_wait = np.mean([r['avg_waiting'] for r in fixed_results])
    dqn_avg_wait = np.mean([r['avg_waiting'] for r in dqn_results])
    improvement = ((fixed_avg_wait - dqn_avg_wait) / fixed_avg_wait) * 100
    
    print(f"Fixed-Time Avg Waiting: {fixed_avg_wait:.2f}s")
    print(f"DQN Avg Waiting: {dqn_avg_wait:.2f}s")
    print(f"Improvement: {improvement:.1f}%")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--compare':
        compare_with_fixed_time(episodes=3)
    else:
        test_agent('models/traffic_dqn.pth', episodes=5, use_gui=True)