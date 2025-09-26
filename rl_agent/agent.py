import numpy as np
import random
from collections import defaultdict

class QLearningAgent:
    """
    Q-Learning agent using discrete state space and Q-table.
    """
    
    def __init__(self, state_size, action_size, learning_rate=0.1, 
                 discount_factor=0.9, epsilon_start=1.0, epsilon_min=0.01, 
                 epsilon_decay=0.995):
        """
        Initialize the Q-Learning agent.
        
        Args:
            state_size: Number of state features (should be 3 for our setup)
            action_size: Number of possible actions (should be 2: KEEP/SWITCH)
            learning_rate: How fas t the agent learns (0.0 to 1.0)
            discount_factor: How much future rewards matter (0.0 to 1.0)
            epsilon_start: Initial exploration rate
            epsilon_min: Minimum exploration rate
            epsilon_decay: How fas t exploration decreases
        """
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        
        # --- UPDATED: Q-table using defaultdict for automatic state creation ---
        # This creates new Q-values automatically when new states are encountered
        self.q_table = defaultdict(lambda: [0.0] * self.action_size)
        
        # --- UPDATED: Track state-action visit counts for debugging ---
        self.state_action_counts = defaultdict(lambda: [0] * self.action_size)
        self.total_actions = 0
        
        print(f"🧠 Q-Learning Agent initialized:")
        print(f"   State size: {state_size}")
        print(f"   Action size: {action_size}")
        print(f"   Learning rate: {learning_rate}")
        print(f"   Discount factor: {discount_factor}")
        print(f"   Initial epsilon: {epsilon_start}")
    
    def _state_to_key(self, state):
        """
        Convert state array to a hashable key for Q-table lookup.
        
        Args:
            state: State array (typically 3 values: ns_queue, ew_queue, phase)
        
        Returns:
            tuple: Hashable state key
        """
        # --- UPDATED: Handle both 1D arrays and 2D arrays (from neural network code) ---
        if len(state.shape) > 1:
            state = state.flatten()
        
        # Convert to tuple of integers for discrete state space
        return tuple(int(x) for x in state)
    
    def choose_action(self, state, valid_actions=None):
        """
        Choose action using epsilon-greedy policy.
        
        Args:
            state: Current state
            valid_actions: List of valid actions (optional, defaults to all actions)
        
        Returns:
            int: Selected action (0=KEEP, 1=SWITCH)
        """
        if valid_actions is None:
            valid_actions = list(range(self.action_size))
        
        state_key = self._state_to_key(state)
        self.total_actions += 1
        
        # --- UPDATED: Epsilon-greedy action selection ---
        if random.random() < self.epsilon:
            # Explore: choose random action
            action = random.choice(valid_actions)
        else:
            # Exploit: choose best known action
            q_values = self.q_table[state_key]
            
            # Filter Q-values for valid actions only
            valid_q_values = [(action, q_values[action]) for action in valid_actions]
            
            # Choose action with highest Q-value
            action = max(valid_q_values, key=lambda x: x[1])[0]
        
        # --- UPDATED: Track action usage ---
        self.state_action_counts[state_key][action] += 1
        
        return action
    
    def learn(self, state, action, reward, next_state):
        """
        Update Q-table based on experience.
        
        Args:
            state: Previous state
            action: Action taken
            reward: Reward received
            next_state: New state after action
        """
        state_key = self._state_to_key(state)
        next_state_key = self._state_to_key(next_state)
        
        # Current Q-value for the state-action pair
        current_q = self.q_table[state_key][action]
        
        # Maximum Q-value for the next state (best future action)
        max_next_q = max(self.q_table[next_state_key])
        
        # --- UPDATED: Q-learning update rule ---
        # Q(s,a) = Q(s,a) + α * [R + γ * max(Q(s',a')) - Q(s,a)]
        td_target = reward + self.discount_factor * max_next_q
        td_error = td_target - current_q
        new_q_value = current_q + self.learning_rate * td_error
        
        # Update Q-table
        self.q_table[state_key][action] = new_q_value
        
        # --- UPDATED: Decay exploration rate ---
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def get_q_value(self, state, action):
        """
        Get Q-value for a specific state-action pair.
        
        Args:
            state: State to query
            action: Action to query
        
        Returns:
            float: Q-value
        """
        state_key = self._state_to_key(state)
        return self.q_table[state_key][action]
    
    def get_best_action(self, state, valid_actions=None):
        """
        Get the best action for a state (no exploration).
        
        Args:
            state: Current state
            valid_actions: List of valid actions (optional)
        
        Returns:
            int: Best action
        """
        if valid_actions is None:
            valid_actions = list(range(self.action_size))
        
        state_key = self._state_to_key(state)
        q_values = self.q_table[state_key]
        
        # Find action with highest Q-value among valid actions
        valid_q_values = [(action, q_values[action]) for action in valid_actions]
        best_action = max(valid_q_values, key=lambda x: x[1])[0]
        
        return best_action
    
    def get_stats(self):
        """
        Get training statistics.
        
        Returns:
            dict: Statistics about the agent's learning
        """
        return {
            'total_states_learned': len(self.q_table),
            'total_actions_taken': self.total_actions,
            'current_epsilon': self.epsilon,
            'avg_q_value': np.mean([max(q_vals) for q_vals in self.q_table.values()]) if self.q_table else 0,
            'exploration_ratio': self.epsilon
        }
    
    def print_stats(self):
        """Print current learning statistics."""
        stats = self.get_stats()
        print(f"📊 Agent Statistics:")
        print(f"   States learned: {stats['total_states_learned']}")
        print(f"   Actions taken: {stats['total_actions_taken']}")
        print(f"   Current epsilon: {stats['current_epsilon']:.3f}")
        print(f"   Average max Q-value: {stats['avg_q_value']:.2f}")
    
    def save_human_readable_policy(self, filename="learned_policy.txt"):
        """
        Save the learned policy in a human-readable format.
        
        Args:
            filename: File to save the policy to
        """
        try:
            with open(filename, 'w') as f:
                f.write("🚦 Learned Traffic Signal Policy\n")
                f.write("=" * 50 + "\n\n")
                f.write("State Format: (NS_Queue, EW_Queue, Current_Phase)\n")
                f.write("Actions: 0=KEEP current phase, 1=SWITCH phase\n")
                f.write("Q-values show expected future reward\n\n")
                
                # Sort states for better readability
                sorted_states = sorted(self.q_table.items())
                
                for state_key, q_values in sorted_states:
                    f.write(f"State {state_key}:\n")
                    for action, q_val in enumerate(q_values):
                        action_name = "KEEP" if action == 0 else "SWITCH"
                        f.write(f"  {action_name:6}: {q_val:7.3f}")
                        if action == np.argmax(q_values):
                            f.write(" <- BEST")
                        f.write("\n")
                    f.write("\n")
                
                # Add summary statistics
                stats = self.get_stats()
                f.write(f"\nTraining Summary:\n")
                f.write(f"Total states learned: {stats['total_states_learned']}\n")
                f.write(f"Total actions taken: {stats['total_actions_taken']}\n")
                f.write(f"Final exploration rate: {stats['current_epsilon']:.3f}\n")
            
            print(f"📄 Human-readable policy saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving policy: {e}")