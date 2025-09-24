import os
import pandas as pd
import matplotlib.pyplot as plt

def plot_training_results(log_file='training_log.csv'):
    if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
        print(f"Log file '{log_file}' is empty or does not exist. Skipping plot.")
        return
    
    data = pd.read_csv(log_file)
    if data.empty:
        print("Log file is empty. Skipping plot.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(data['episode'], data['total_reward'])
    plt.title('Total Reward per Episode')
    plt.xlabel('Episode')
    plt.ylabel('Total Reward')
    plt.grid(True)
    
    data['reward_moving_avg'] = data['total_reward'].rolling(window=50, min_periods=1).mean()
    plt.plot(data['episode'], data['reward_moving_avg'], label='50-episode Moving Average', color='red', linewidth=2)
    
    plt.legend()
    plt.savefig('training_progress.png')
    print("Training graph saved to training_progress.png")
    plt.show()

if __name__ == "__main__":
    plot_training_results()