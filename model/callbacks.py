from stable_baselines3.common.callbacks import BaseCallback

class CustomCallback(BaseCallback):
    """
    A custom callback that can be used for logging, saving, or other tasks during training.
    """
    def __init__(self, verbose=0):
        super(CustomCallback, self).__init__(verbose)
        # Your initialization code here

    def _on_step(self) -> bool:
        # This method will be called by the model after each call to `env.step()`.
        return True # Continue training