# train.py
import os
import sys
import csv
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from rl_agent.environment import SumoEnvironment
from rl_agent.agent import Agent

def plot_training_results():
    """Reads the log file and plots the training performance."""
    log_file = 'training_log.csv'
    if os.path.exists(log_file):
        try:
            data = pd.read_csv(log_file)
            if not data.empty:
                plt.figure(figsize=(12, 6))
                plt.plot(data['episode'], data['total_reward'])
                plt.title('Total Reward per Episode')
                plt.xlabel('Episode')
                plt.ylabel('Total Reward')
                plt.grid(True)
                plt.savefig('training_progress.png')
                print("Training graph saved to training_progress.png")
                plt.show()
        except pd.errors.EmptyDataError:
            print("Log file is empty. Skipping plot.")

if __name__ == "__main__":
    episodes = 20
    batch_size = 32
    log_file_path = 'training_log.csv'

    start_time = datetime.now()
    print(f"--- Training started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ---")

    with open(log_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['episode', 'total_reward', 'timesteps', 'epsilon'])

    model_dir = "rl_agent/models"
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    env = SumoEnvironment(use_gui=False)
    agent = Agent(state_size=env.state_size, action_size=env.action_size)
    
    for e in range(episodes):
        state = env.reset()
        done = False
        total_reward = 0
        time = 0
        
        while not done:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            
            if reward != 0:
                total_reward += reward
            time += 1
            
            # --- MODIFIED HEARTBEAT ---
            # This is a more robust print statement that won't cause a hang
            if time % 100 == 0:
                print(f"  ...step {time}...")

            if done:
                with open(log_file_path, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([e + 1, total_reward, time, agent.epsilon])
                print(f"\nEpisode: {e+1}/{episodes}, Total Reward: {total_reward:.2f}, Timesteps: {time}, Epsilon: {agent.epsilon:.2}")
                break
            
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)
        
        save_path = os.path.join(model_dir, f"traffic-model-e{e+1}.weights.h5")
        agent.save(save_path)
        print(f"Model saved to {save_path}")
            
    env.close()
    
    end_time = datetime.now()
    print(f"--- Training ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    print(f"Total training time: {end_time - start_time}")

    plot_training_results()