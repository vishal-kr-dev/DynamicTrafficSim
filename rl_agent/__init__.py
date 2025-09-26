"""
SUMO RL Training Package

This package provides ultra reinforcement learning training for SUMO traffic simulations.
Optimized for quick prototyping and testing before scaling to complex scenarios.

Key Features:
- Q-table learning (fas ter than neural networks for small state spaces)
- Discrete state space (27 possible states total)
- Large simulation time steps (10s instead of 1s)
- Pre-generated consistent traffic patterns
- Simple 2-action control (KEEP/SWITCH signal phase)

Usage:
    from f ast_rl.f ast_environment import SumoEnvironment
    from fa st_rl.fas t_agent import QLearningAgent
    
    env = SumoEnvironment(use_gui=False, simulation_step=10)
    agent = QLearningAgent(state_size=3, action_size=2)
    
    # Training loop
    state = env.reset()
    action = agent.choose_action(state)
    next_state, reward, wait_time = env.step(action)
    agent.learn(state, action, reward, next_state)

Expected Performance:
- 50 episodes in 3-5 minutes
- Convergence within 20-30 episodes
- ~90% reduction in training time vs neural networks
"""

__version__ = "1.0.0"
__author__ = "SUMO RL Training System"

from rl_agent.environment import SumoEnvironment
from rl_agent.agent import QLearningAgent

__all__ = ['SumoEnvironment', 'QLearningAgent']

# Package metadata
PACKAGE_INFO = {
    'name': 'rl_agent',
    'version': __version__,
    'description': 'SUMO RL training for traffic signal control',
    'optimization_level': 'Maximum Speed',
    'expected_training_time': '3-5 minutes for 50 episodes',
    'state_space_size': 27,  # 3 x 3 x 3 (NS_queue x EW_queue x phase)
    'action_space_size': 2,  # KEEP, SWITCH
    'algorithm': 'Q-Learning with discrete state space'
}

def print_package_info():
    """Print information about the RL package."""
    print("🚦 SUMO RL Package Information")
    print("=" * 40)
    for key, value in PACKAGE_INFO.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("=" * 40)

# Optimization settings (can be imported and modified)
DEFAULT_CONFIG = {
    'simulation_step': 10,      # Seconds per step
    'episode_length': 600,      # Seconds per episode
    'min_phase_duration': 20,   # Minimum green time
    'max_phase_duration': 120,  # Maximum green time
    'yellow_duration': 4,       # Yellow light time
    'queue_buckets': [0, 3, 8], # State discretization thresholds
    'learning_rate': 0.1,       # Q-learning rate
    'discount_factor': 0.9,     # Future reward importance
    'epsilon_start': 0.9,       # Initial exploration
    'epsilon_min': 0.05,        # Minimum exploration
    'epsilon_decay': 0.95       # Exploration decay
}

# Performance targets
PERFORMANCE_TARGETS = {
    'episodes_to_convergence': 30,
    'minutes_per_50_episodes': 5,
    'speedup_vs_neural_network': 10,
    'speedup_vs_1s_steps': 10,
    'memory_usage_mb': 50,
    'cpu_usage_percent': 25
}

def validate_environment():
    """Check if the environment is ready for  training."""
    import os
    
    issues = []
    
    # Check SUMO installation
    if 'SUMO_HOME' not in os.environ:
        issues.append("SUMO_HOME environment variable not set")
    
    # Check required directories exist
    if not os.path.exists('rl_agent'):
        issues.append("rl_agent directory not found")
    
    # Check Python packages
    try:
        import numpy
        import pandas
        import matplotlib
    except ImportError as e:
        issues.append(f"Missing Python package: {e}")
    
    if issues:
        print("❌ Environment validation failed:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Environment validation passed!")
        return True

if __name__ == "__main__":
    print_package_info()
    print()
    validate_environment()