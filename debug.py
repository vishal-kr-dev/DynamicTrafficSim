import yaml
from sumo_env.env import SumoEnv
import random

def run_debug():
    """
    Loads the environment and runs a few random steps to check for errors.
    """
    print("--- Starting Environment Debugger ---")
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create the environment
    env = SumoEnv(config, use_gui=False)

    try:
        # Try to reset the environment (this will load a random route file)
        obs, info = env.reset()
        print("[SUCCESS] Environment reset successfully.")

        # Try to run a few steps with random actions
        for i in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                print(f"Episode finished after {i+1} steps.")
                break
        
        print("[SUCCESS] Environment ran for 10 steps without crashing.")

    except Exception as e:
        print("\n--- !!! AN ERROR OCCURRED !!! ---")
        print(f"The error happened during the test run.")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print("Please check the SUMO output above for the root cause (e.g., 'no valid route').")
    
    finally:
        env.close()
        print("\n--- Debugger Finished ---")


if __name__ == '__main__':
    run_debug()