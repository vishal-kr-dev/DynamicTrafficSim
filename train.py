import yaml
from stable_baselines3.common.env_checker import check_env
from sumo_env.env import SumoEnv
from model.dqn_agent import DQNAgent

def train_model():
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create and check the environment
    env = SumoEnv(config, use_gui=False)
    check_env(env)

    # Create and train the agent
    agent = DQNAgent(env, config)
    print("Starting model training...")
    agent.train()
    print("Training complete.")

    # Save the final model
    agent.save_model()
    
    env.close()

if __name__ == '__main__':
    train_model()