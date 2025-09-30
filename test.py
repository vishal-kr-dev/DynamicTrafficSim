import yaml
from sumo_env.env import SumoEnv
from model.dqn_agent import DQNAgent

def test_model():
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create the environment with GUI for visualization
    env = SumoEnv(config, use_gui=True)

    # Create the agent and load the trained model
    agent = DQNAgent(env, config)
    agent.load_model()

    # Run one test episode
    print("Starting test simulation...")
    obs, _ = env.reset()
    done = False
    
    while not done:
        action = agent.predict(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated

    print("Test simulation finished.")
    env.close()

if __name__ == '__main__':
    test_model()