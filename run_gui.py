from rl_agent.environment import SumoEnvironment
from rl_agent.agent import Agent
import time

if __name__ == "__main__":
    # Initialize environment and agent
    env = SumoEnvironment(use_gui=True, delay=200)
    agent = Agent(state_size=env.state_size, action_size=env.action_size)
    
    # Load the pre-trained model weights
    try:
        agent.load("rl_agent/models/traffic-model-e50.weights.h5") # Load the final model from training
        agent.epsilon = 0.0 # Turn off exploration
    except FileNotFoundError:
        print("Error: Model not found. Please run train.py first.")
        exit()

    state = env.reset()
    done = False
    
    while not done:
        action = agent.act(state) # Use the learned policy
        next_state, reward, done = env.step(action)
        state = next_state
        time.sleep(0.1) # Slow down for visualization
        
    env.close()