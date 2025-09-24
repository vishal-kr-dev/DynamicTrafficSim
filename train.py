import os, sys, csv, time
from datetime import datetime
from rl_agent.environment import SumoEnvironment
from rl_agent.agent import Agent
from generate_routes import generate_route_files # Import the function

if __name__ == "__main__":
    episodes = 1; batch_size = 32; log_file_path = 'training_log.csv'

    # --- Pre-generate route files ---
    generate_route_files(0, episodes)

    start_time = datetime.now()
    print(f"--- Training started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ---")

    with open(log_file_path, 'w', newline='') as file:
        writer = csv.writer(file); writer.writerow(['episode', 'total_reward', 'timesteps'])
    
    model_dir = "rl_agent/models"
    if not os.path.exists(model_dir): os.makedirs(model_dir)

    env = SumoEnvironment(use_gui=False)
    agent = Agent(state_size=env.state_size, action_size=env.action_size)
    
    for e in range(episodes):
        state = env.reset(episode_num=e)
        done = False; total_reward = 0; timesteps = 0
        
        while not done:
            valid_actions = env.get_valid_actions()
            action = agent.act(state, valid_actions)
            next_state, reward, done = env.step(action)
            agent.remember(state, action, reward, next_state, done)
            state = next_state; total_reward += reward; timesteps += 1
            if len(agent.memory) > batch_size: agent.replay(batch_size)
        
        with open(log_file_path, 'a', newline='') as file:
            writer = csv.writer(file); writer.writerow([e + 1, total_reward, timesteps])
        print(f"Episode: {e+1}/{episodes} | Total Reward: {total_reward:.2f}")

        agent.save(os.path.join(model_dir, f"traffic-model-e{e+1}.weights.h5"))
            
    env.close()
    
    end_time = datetime.now()
    print(f"--- Training ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    print(f"Total training time: {end_time - start_time}")
    print("\nTo see the graph of the training results, run: python plot_results.py")