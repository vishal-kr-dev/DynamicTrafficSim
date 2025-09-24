import os, sys
from rl_agent.environment import SumoEnvironment
from rl_agent.agent import Agent
import time

if __name__ == "__main__":
    # --- Load the best model ---
    model_to_load = "traffic-model-e500.weights.h5" 
    model_path = os.path.join("rl_agent/models", model_to_load)

    if not os.path.exists(model_path):
        sys.exit(f"Error: Model not found at {model_path}. Please train the model first.")

    # --- Initialize Environment and Agent ---
    env = SumoEnvironment(use_gui=True, delay=100)
    agent = Agent(state_size=env.state_size, action_size=env.action_size)
    
    # Load the pre-trained model weights and turn off random exploration
    agent.load(model_path)
    agent.epsilon = 0.0 
    print(f"Loaded model: {model_to_load}")

    # Run a single episode with the trained agent
    state = env.reset(episode_num=random.randint(0, 499)) # Use a random traffic scenario
    done = False
    
    while not done:
        valid_actions = env.get_valid_actions()
        action = agent.act(state, valid_actions)
        next_state, reward, done = env.step(action)
        state = next_state
        
    env.close()