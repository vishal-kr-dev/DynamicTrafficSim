import os
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
import json
from datetime import datetime

# SUMO environment check
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci
import sumolib

class DQNNetwork(nn.Module):
    def __init__(self, state_size, action_size):
        super(DQNNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, 64)
        self.fc4 = nn.Linear(64, action_size)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        return self.fc4(x)

class TrafficEnvironment:
    def __init__(self, net_file, route_file, use_gui=False):
        self.net_file = net_file
        self.route_file = route_file
        self.use_gui = use_gui
        # EDITED: Get traffic light ID dynamically from network
        self.tls_id = None
        
        # EDITED: Traffic phases with yellow transitions (8 phases total)
        # Green phases: 0=North, 2=East, 4=South, 6=West
        # Yellow phases: 1, 3, 5, 7 (auto-handled by SUMO)
        self.phases = [0, 2, 4, 6]  # DQN chooses from 4 green phases
        self.min_green_duration = 10
        
        self.current_phase = 0
        self.time_since_last_phase_change = 0
        
        # Data logging
        self.episode_data = {
            'waiting_times': [],
            'queue_lengths': [],
            'phase_changes': [],
            'vehicles_passed': {'passenger': 0, 'emergency': 0, 'bus': 0, 'truck': 0},
            'total_vehicles': 0
        }
        
    def start_simulation(self):
        sumo_cmd = ['sumo-gui' if self.use_gui else 'sumo', '-c', 'simulation.sumocfg',
                    '--no-warnings', '--no-step-log', '--time-to-teleport', '-1']
        traci.start(sumo_cmd)
        
        # EDITED: Get actual traffic light ID from simulation
        tls_ids = traci.trafficlight.getIDList()
        if len(tls_ids) == 0:
            raise Exception("No traffic lights found in network")
        self.tls_id = tls_ids[0]  # Use first traffic light
        
        # EDITED: Switch to our custom 'dqn' program
        traci.trafficlight.setProgram(self.tls_id, 'dqn')
        
        # Get available phases from traffic light program
        logic = traci.trafficlight.getAllProgramLogics(self.tls_id)[0]
        available_phases = len(logic.phases)
        
        # Debug: print traffic light info only once
        if not hasattr(self, '_tls_printed'):
            print(f"Traffic light ID: {self.tls_id}, Available phases: {available_phases}")
            self._tls_printed = True
        
    def get_state(self):
        # EDITED: State for 4 directions - [queue_N, queue_E, queue_S, queue_W, current_phase, time_in_phase]
        lanes = ['N2TL_0', 'E2TL_0', 'S2TL_0', 'W2TL_0']  # North, East, South, West
        queue_lengths = [traci.lane.getLastStepHaltingNumber(lane) for lane in lanes]
        
        state = queue_lengths + [self.current_phase, self.time_since_last_phase_change]
        return np.array(state, dtype=np.float32)
    
    def step(self, action):
        # EDITED: Ensure traffic light ID is set
        if self.tls_id is None:
            raise Exception("Traffic light ID not initialized. Call reset() first.")
        
        # Emergency vehicle check - RULE-BASED OVERRIDE
        emergency_override = self._check_emergency_vehicles()
        if emergency_override is not None:
            action = emergency_override
        
        reward = 0
        target_phase = self.phases[action]
        
        # Change phase if needed
        if target_phase != self.current_phase and self.time_since_last_phase_change >= self.min_green_duration:
            self._change_phase(target_phase)
            self.time_since_last_phase_change = 0
        else:
            traci.simulationStep()
            self.time_since_last_phase_change += 1
        
        # Calculate reward (negative waiting time to minimize)
        total_waiting_time = 0
        lanes = ['N2TL_0', 'E2TL_0', 'S2TL_0', 'W2TL_0']  # All four directions
        for lane in lanes:
            total_waiting_time += traci.lane.getWaitingTime(lane)
        
        reward = -total_waiting_time
        
        # Log data
        self._log_step_data(total_waiting_time, lanes)
        
        next_state = self.get_state()
        done = traci.simulation.getMinExpectedNumber() <= 0
        
        return next_state, reward, done
    
    def _check_emergency_vehicles(self):
        """Rule-based emergency vehicle preemption - one direction at a time"""
        # EDITED: Check each direction individually (N=0, E=1, S=2, W=3)
        lanes = {0: ['N2TL_0'], 1: ['E2TL_0'], 2: ['S2TL_0'], 3: ['W2TL_0']}
        
        for action, lane_list in lanes.items():
            for lane in lane_list:
                vehicles = traci.lane.getLastStepVehicleIDs(lane)
                for veh in vehicles:
                    if traci.vehicle.getTypeID(veh) == 'emergency':
                        return action  # Override to emergency vehicle direction
        return None
    
    def _change_phase(self, target_phase):
        """Change phase - SUMO handles yellow transitions automatically"""
        # EDITED: Just set target phase, SUMO transitions through yellow automatically
        traci.trafficlight.setPhase(self.tls_id, target_phase)
        self.current_phase = target_phase
        
        # Wait minimum duration
        for _ in range(self.min_green_duration):
            traci.simulationStep()
        
        # Log phase change with timestamp
        self.episode_data['phase_changes'].append({
            'time': traci.simulation.getTime(),
            'new_phase': target_phase
        })
    
    def _log_step_data(self, waiting_time, lanes):
        """Log important metrics during simulation"""
        self.episode_data['waiting_times'].append(waiting_time)
        
        queue_length = sum([traci.lane.getLastStepHaltingNumber(lane) for lane in lanes])
        self.episode_data['queue_lengths'].append(queue_length)
        
        # Count vehicles passed (departed vehicles)
        for veh_id in traci.simulation.getArrivedIDList():
            veh_type = traci.vehicle.getTypeID(veh_id) if veh_id in traci.vehicle.getIDList() else 'passenger'
            if veh_type in self.episode_data['vehicles_passed']:
                self.episode_data['vehicles_passed'][veh_type] += 1
            self.episode_data['total_vehicles'] += 1
    
    def reset(self):
        if traci.isLoaded():
            traci.close()
        
        # Save episode data before reset (skip first time)
        if self.tls_id is not None:
            self._save_episode_data()
        
        # Reset episode data
        self.episode_data = {
            'waiting_times': [],
            'queue_lengths': [],
            'phase_changes': [],
            'vehicles_passed': {'passenger': 0, 'emergency': 0, 'bus': 0, 'truck': 0},
            'total_vehicles': 0
        }
        
        self.current_phase = 0
        self.time_since_last_phase_change = 0
        self.start_simulation()
        
        # EDITED: Set initial traffic light phase after starting simulation
        if self.tls_id:
            traci.trafficlight.setPhase(self.tls_id, 0)
        
        return self.get_state()
    
    def _save_episode_data(self):
        """Save episode data to JSON file"""
        # EDITED: Skip if no data collected yet
        if not self.episode_data['waiting_times']:
            return
            
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'logs/episode_{timestamp}.json'
        
        summary = {
            'avg_waiting_time': np.mean(self.episode_data['waiting_times']) if self.episode_data['waiting_times'] else 0,
            'avg_queue_length': np.mean(self.episode_data['queue_lengths']) if self.episode_data['queue_lengths'] else 0,
            'total_phase_changes': len(self.episode_data['phase_changes']),
            'vehicles_passed': self.episode_data['vehicles_passed'],
            'total_vehicles': self.episode_data['total_vehicles']
        }
        
        with open(filename, 'w') as f:
            json.dump({'summary': summary, 'details': self.episode_data}, f, indent=2)
    
    def close(self):
        if traci.isLoaded():
            traci.close()

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.batch_size = 32
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = DQNNetwork(state_size, action_size).to(self.device)
        self.target_model = DQNNetwork(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()
        
        self.update_target_model()
    
    def update_target_model(self):
        self.target_model.load_state_dict(self.model.state_dict())
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.model(state)
        return q_values.argmax().item()
    
    def replay(self):
        if len(self.memory) < self.batch_size:
            return 0
        
        minibatch = random.sample(self.memory, self.batch_size)
        
        states = torch.FloatTensor([t[0] for t in minibatch]).to(self.device)
        actions = torch.LongTensor([t[1] for t in minibatch]).to(self.device)
        rewards = torch.FloatTensor([t[2] for t in minibatch]).to(self.device)
        next_states = torch.FloatTensor([t[3] for t in minibatch]).to(self.device)
        dones = torch.FloatTensor([t[4] for t in minibatch]).to(self.device)
        
        current_q = self.model(states).gather(1, actions.unsqueeze(1))
        next_q = self.target_model(next_states).max(1)[0].detach()
        target_q = rewards + (1 - dones) * self.gamma * next_q
        
        loss = self.criterion(current_q.squeeze(), target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def save(self, filename):
        torch.save(self.model.state_dict(), filename)
    
    def load(self, filename):
        self.model.load_state_dict(torch.load(filename))
        self.update_target_model()

def train_agent(episodes=100):
    env = TrafficEnvironment('intersection.net.xml', 'traffic.rou.xml', use_gui=False)
    # EDITED: 4 actions now (N, E, S, W) instead of 2
    agent = DQNAgent(state_size=6, action_size=4)
    
    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        steps = 0
        
        while True:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            steps += 1
            
            loss = agent.replay()
            
            if done:
                break
        
        agent.update_target_model()
        
        if agent.epsilon > agent.epsilon_min:
            agent.epsilon *= agent.epsilon_decay
        
        # EDITED: Minimal training progress log every 10 episodes
        if episode % 10 == 0:
            print(f"Ep {episode}/{episodes} | Reward: {total_reward:.1f} | ε: {agent.epsilon:.3f} | Steps: {steps}")
    
    agent.save('models/traffic_dqn.pth')
    env.close()
    print("Training complete. Model saved.")

if __name__ == "__main__":
    os.makedirs('models', exist_ok=True)
    train_agent(episodes=100)