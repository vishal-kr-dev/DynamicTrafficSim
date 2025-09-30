from stable_baselines3 import DQN
import os

class DQNAgent:
    def __init__(self, env, config):
        self.env = env
        self.config = config
        self.model_path = config['paths']['model_save_path']
        self.model = self._setup_model()

    def _setup_model(self):
        return DQN(
            env=self.env,
            policy=self.config['dqn']['policy'],
            learning_rate=self.config['dqn']['learning_rate'],
            buffer_size=self.config['dqn']['buffer_size'],
            learning_starts=self.config['dqn']['learning_starts'],
            batch_size=self.config['dqn']['batch_size'],
            gamma=self.config['dqn']['gamma'],
            train_freq=tuple(self.config['dqn']['train_freq']),
            target_update_interval=self.config['dqn']['target_update_interval'],
            exploration_fraction=self.config['dqn']['exploration_fraction'],
            exploration_final_eps=self.config['dqn']['exploration_final_eps'],
            verbose=self.config['dqn']['verbose']
        )

    def train(self):
        total_timesteps = self.config['dqn']['total_timesteps']
        self.model.learn(total_timesteps=total_timesteps)

    def save_model(self):
        model_dir = os.path.dirname(self.model_path)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        self.model.save(self.model_path)
        print(f"Model saved to {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = DQN.load(self.model_path, env=self.env)
            print(f"Model loaded from {self.model_path}")
        else:
            print("No saved model found. Starting with a new model.")

    def predict(self, obs):
        action, _states = self.model.predict(obs, deterministic=True)
        return action