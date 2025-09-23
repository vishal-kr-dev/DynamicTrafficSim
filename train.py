import os
import sys
import csv # For logging data
import pandas as pd # For reading the log file
import matplotlib.pyplot as plt # For generating the graph
from rl_agent.environment import SumoEnvironment
from rl_agent.agent import Agent

# --- Graph Generation Function ---
def plot_training_results():
    """Reads the log file and plots the training performance."""
    log_file = 'training_log.csv'
    if os.path.exists(log_file):
        data = pd.read_csv(log_file)
        plt.figure(figsize=(12, 6))
        plt.plot(data['episode'], data['total_reward'])
        plt.title('Total Reward per Episode')
        plt.xlabel('Episode')
        plt.ylabel('Total Reward (Negative Wait Time)')
        plt.grid(True)
        plt.savefig('training_progress.png') # Saves the graph as an image
        print("Training graph saved to training_progress.png")
        plt.show()

if __name__ == "__main__":
    # --- Training Parameters ---
    episodes = 50 
    batch_size = 32
    log_file_path = 'training_log.csv'

    # --- CSV Log File Setup ---
    with open(log_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['episode', 'total_reward', 'timesteps', 'epsilon'])

    # --- Model Save Folder Setup ---
    model_dir = "rl_agent/models"
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    # --- Initialize Agent and Environment ---
    env = SumoEnvironment(use_gui=False)
    agent = Agent(state_size=env.state_size, action_size=env.action_size)
    
    # --- Main Training Loop (Episodes) ---
    for e in range(episodes):
        state = env.reset()
        done = False
        total_reward = 0
        time = 0
        
        # --- Inner Loop (Steps within one episode) ---
        while not done:
            action = agent.act(state) # Agent chooses an action
            next_state, reward, done = env.step(action) # Agent performs the action
            agent.remember(state, action, reward, next_state, done) # Agent stores the experience
            state = next_state # Update the state
            
            total_reward += reward # Accumulate reward for this episode
            time += 1 # Count the timesteps
            
            if done:
                # --- Log Data at Episode End ---
                with open(log_file_path, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([e + 1, total_reward, time, agent.epsilon])
                
                print(f"episode: {e+1}/{episodes}, total_reward: {total_reward:.2f}, timesteps: {time}, epsilon: {agent.epsilon:.2}")
                break
            
            # --- Agent Learning Step ---
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)
        
        # --- Save Model Periodically ---
        if (e+1) % 10 == 0:
            save_path = os.path.join(model_dir, f"traffic-model-e{e+1}.weights.h5")
            agent.save(save_path)
            print(f"Model saved to {save_path}")
            
    # --- Cleanup and Final Actions ---
    env.close() # Close the SUMO simulation
    plot_training_results() # Generate the final performance graph