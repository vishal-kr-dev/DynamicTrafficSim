import os
import sys
import time
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from rl_agent.environment import SumoEnvironment
from rl_agent.agent import QLearningAgent

def plot_training_results():
    """Plots training performance from log data."""
    log_file = 'training_log.csv'
    if os.path.exists(log_file):
        try:
            data = pd.read_csv(log_file)
            if not data.empty:
                plt.figure(figsize=(15, 5))
                
                # Plot 1: Total Reward
                plt.subplot(1, 3, 1)
                plt.plot(data['episode'], data['total_reward'], 'b-', linewidth=2)
                plt.title('Total Reward per Episode')
                plt.xlabel('Episode')
                plt.ylabel('Total Reward')
                plt.grid(True, alpha=0.3)
                
                # Plot 2: Average Wait Time
                plt.subplot(1, 3, 2)
                plt.plot(data['episode'], data['avg_wait_time'], 'r-', linewidth=2)
                plt.title('Average Wait Time per Episode')
                plt.xlabel('Episode')
                plt.ylabel('Wait Time (seconds)')
                plt.grid(True, alpha=0.3)
                
                # Plot 3: Exploration Rate
                plt.subplot(1, 3, 3)
                plt.plot(data['episode'], data['epsilon'], 'g-', linewidth=2)
                plt.title('Exploration Rate (Epsilon)')
                plt.xlabel('Episode')
                plt.ylabel('Epsilon')
                plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                plt.savefig('training_progress.png', dpi=150, bbox_inches='tight')
                print("📊 Training graphs saved to training_progress.png")
                plt.show()
        except Exception as e:
            print(f"❌ Error plotting results: {e}")

def save_agent_model(agent, filepath):
    """Saves the Q-table model to disk."""
    try:
        with open(filepath, 'wb') as f:
            pickle.dump({
                'q_table': agent.q_table,
                'epsilon': agent.epsilon,
                'state_action_counts': getattr(agent, 'state_action_counts', {}),
                'training_episodes': getattr(agent, 'training_episodes', 0)
            }, f)
        print(f"💾 Model saved to {filepath}")
    except Exception as e:
        print(f"❌ Error saving model: {e}")

def load_agent_model(agent, filepath):
    """Loads a Q-table model from disk."""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            agent.q_table = data['q_table']
            agent.epsilon = data['epsilon']
            if 'state_action_counts' in data:
                agent.state_action_counts = data['state_action_counts']
            print(f"📂 Model loaded from {filepath}")
            return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
    return False

if __name__ == "__main__":
    # --- TRAINING CONFIGURATION ---
    EPISODES = 50              # Number of training episodes
    EPISODE_LENGTH = 600       # Seconds of simulated traffic per episode (10 minutes)
    SIMULATION_STEP = 10       # Seconds per simulation step (10x speed boost)
    USE_GUI = False            # Set to True to watch training (slower)
    SAVE_FREQUENCY = 10        # Save model every N episodes
    
    # --- UPDATED: Enhanced logging with more metrics ---
    print("🚦 SUMO RL Traffic Signal Training")
    print("=" * 50)
    print(f"Episodes: {EPISODES}")
    print(f"Episode length: {EPISODE_LENGTH}s ({EPISODE_LENGTH//60} minutes)")
    print(f"Simulation step: {SIMULATION_STEP}s")
    print(f"Expected total time: ~{(EPISODES * EPISODE_LENGTH * 0.1)/60:.1f} minutes")
    print("=" * 50)

    # Setup logging
    log_data = []
    
    # Create model directory
    model_dir = "rl_agent/models"
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    
    # Initialize environment and agent
    print("🏗️  Initializing environment...")
    env = SumoEnvironment(use_gui=USE_GUI, simulation_step=SIMULATION_STEP)
    
    print("🧠 Initializing Q-Learning agent...")
    agent = QLearningAgent(
        state_size=env.get_state_size(),
        action_size=env.get_action_size(),
        learning_rate=0.1,      # Higher learning rate for fas ter convergence
        discount_factor=0.9,    # Slightly lower for fas ter adaptation
        epsilon_start=0.9,      # High exploration initially
        epsilon_min=0.05,       # Some exploration always
        epsilon_decay=0.95      # Moderate decay
    )
    
    # Try to load existing model
    model_path = os.path.join(model_dir, "traffic_model.pkl")
    if load_agent_model(agent, model_path):
        print("🔄 Continuing from existing model...")
    
    # --- TRAINING LOOP ---
    start_time = time.time()
    print(f"\n🚀 Training started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    for episode in range(EPISODES):
        episode_start = time.time()
        
        # Reset environment for new episode
        state = env.reset()
        total_reward = 0
        steps = 0
        total_wait_time = 0
        
        # --- UPDATED: Added progress tracking within episodes ---
        max_steps = EPISODE_LENGTH // SIMULATION_STEP
        
        # Run episode
        for step in range(max_steps):
            # Agent chooses action
            action = agent.choose_action(state)
            
            # Take action in environment
            next_state, reward, wait_time = env.step(action)
            
            # Agent learns from experience
            agent.learn(state, action, reward, next_state)
            
            # Update tracking variables
            state = next_state
            total_reward += reward
            total_wait_time += wait_time
            steps += 1
            
            # --- UPDATED: Progress indicator for long episodes ---
            if step % 10 == 0 and steps > 10:
                progress = (step / max_steps) * 100
                print(f"\r  Episode {episode+1}: {progress:.1f}% complete", end="")
        
        episode_time = time.time() - episode_start
        avg_wait_time = total_wait_time / steps if steps > 0 else 0
        
        # --- UPDATED: Enhanced episode logging ---
        print(f"\r✅ Episode {episode+1:2d}/{EPISODES} | "
              f"Reward: {total_reward:6.1f} | "
              f"Avg Wait: {avg_wait_time:5.1f}s | "
              f"Epsilon: {agent.epsilon:.3f} | "
              f"Time: {episode_time:.1f}s")
        
        # Log episode data
        log_data.append({
            'episode': episode + 1,
            'total_reward': total_reward,
            'avg_wait_time': avg_wait_time,
            'steps': steps,
            'epsilon': agent.epsilon,
            'episode_time': episode_time
        })
        
        # Save model periodically
        if (episode + 1) % SAVE_FREQUENCY == 0:
            save_agent_model(agent, model_path)
    
    # --- TRAINING COMPLETE ---
    total_time = time.time() - start_time
    print("-" * 50)
    print(f"🎉 Training completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Total training time: {total_time/60:.2f} minutes")
    print(f"📈 Average time per episode: {total_time/EPISODES:.2f} seconds")
    
    # Save final model and logs
    save_agent_model(agent, model_path)
    
    # --- UPDATED: Enhanced data export ---
    df = pd.DataFrame(log_data)
    df.to_csv('training_log.csv', index=False)
    print("📊 Training log saved to training_log.csv")
    
    # Close environment
    env.close()
    
    # Plot results
    print("\n📊 Generating training plots...")
    plot_training_results()
    
    print("\n🎯 Training Summary:")
    print(f"   Final epsilon (exploration): {agent.epsilon:.3f}")
    print(f"   Q-table size: {len(agent.q_table)} states learned")
    print(f"   Average reward (last 10): {df['total_reward'].tail(10).mean():.1f}")
    print(f"   Average wait time (last 10): {df['avg_wait_time'].tail(10).mean():.1f}s")
    print("\n✨ Ready for deployment or further training!")