# train_parallel.py
import os
import sys
import time
import csv
import pandas as pd
import matplotlib.pyplot as plt
import re
import glob
import multiprocessing as mp
from rl_agent.environment import SumoEnvironment
from rl_agent.agent import Agent

# --- Graph Generation Function ---
def plot_training_results(log_file='training_log_parallel.csv'):
    if not os.path.exists(log_file) or os.path.getsize(log_file) == 0: return
    data = pd.read_csv(log_file)
    if data.empty: return
    plt.figure(figsize=(12, 6)); plt.plot(data['episode'], data['total_reward']); plt.title('Total Reward per Episode')
    plt.xlabel('Episode'); plt.ylabel('Total Reward'); plt.grid(True); plt.savefig('training_progress.png')
    print("Training graph saved to training_progress.png"); plt.close()

# --- Worker process for parallel data collection ---
def worker(experience_queue, worker_id):
    env = SumoEnvironment(use_gui=False, worker_id=worker_id)
    agent = Agent(state_size=env.state_size, action_size=env.action_size)
    while True:
        state = env.reset()
        done = False; total_reward = 0; timesteps = 0
        while not done:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            experience_queue.put((state, action, reward, next_state, done))
            state = next_state; total_reward += reward; timesteps += 1
        experience_queue.put(('episode_done', {'reward': total_reward, 'timesteps': timesteps}))

if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    episodes_to_run = 250; batch_size = 64; log_file_path_base = 'training_log_parallel.csv'
    
    IN_COLAB = 'google.colab' in sys.modules
    project_base_path = "/content/drive/MyDrive/DynamicTrafficSim" if IN_COLAB else "."
    if IN_COLAB: from google.colab import drive; drive.mount('/content/drive')
        
    model_dir = os.path.join(project_base_path, "models"); log_file_path = os.path.join(project_base_path, log_file_path_base)
    if not os.path.exists(model_dir): os.makedirs(model_dir)

    main_agent = Agent(state_size=5, action_size=2)
    start_episode = 0
    model_files = glob.glob(os.path.join(model_dir, "traffic-model-e*.weights.h5"))
    if model_files:
        latest_model = max(model_files, key=os.path.getctime)
        start_episode = int(re.search(r'e(\d+)', latest_model).group(1))
        print(f"Resuming training from model: {latest_model} at episode {start_episode}")
        main_agent.load(latest_model); main_agent.epsilon *= (main_agent.epsilon_decay ** start_episode)
    else:
        print("Starting training from scratch.")
        with open(log_file_path, 'w', newline='') as file: writer = csv.writer(file); writer.writerow(['episode', 'total_reward', 'timesteps'])
            
    num_workers = max(1, mp.cpu_count() - 1)
    experience_queue = mp.Queue(maxsize=1000)
    worker_processes = [mp.Process(target=worker, args=(experience_queue, i)) for i in range(num_workers)]
    for p in worker_processes: p.start()
    print(f"Started {num_workers} worker processes for data collection.")

    episodes_completed = start_episode; learning_steps = 0
    while episodes_completed < episodes_to_run:
        experience = experience_queue.get()
        if isinstance(experience[0], str) and experience[0] == 'episode_done':
            episodes_completed += 1; stats = experience[1]
            with open(log_file_path, 'a', newline='') as file: writer = csv.writer(file); writer.writerow([episodes_completed, stats['reward'], stats['timesteps']])
            print(f"\n--- Episode {episodes_completed}/{episodes_to_run} complete. Reward: {stats['reward']:.2f} ---")
            if episodes_completed > 0 and episodes_completed % 10 == 0: main_agent.save(os.path.join(model_dir, f"traffic-model-e{episodes_completed}.weights.h5"))
            if episodes_completed > 0 and episodes_completed % 50 == 0: plot_training_results(log_file_path)
            continue
        state, action, reward, next_state, done = experience
        main_agent.remember(state, action, reward, next_state, done)
        if len(main_agent.memory) > batch_size:
            main_agent.replay(batch_size); learning_steps += 1
            if learning_steps % 200 == 0: print(f". (step {learning_steps}, memory: {len(main_agent.memory)}, epsilon: {main_agent.epsilon:.2f})", end='', flush=True)

    for p in worker_processes: p.terminate()
    print("\nTraining complete. Final model saved.")
    plot_training_results(log_file_path)