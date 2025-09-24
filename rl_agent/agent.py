# rl_agent/agent.py
import numpy as np
import random
from collections import deque
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input, Lambda
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import backend as K

class Agent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()

        # "Warm up" the model to prevent hangs on first prediction
        print("Warming up agent's brain...")
        dummy_state = np.zeros((1, self.state_size))
        self.model.predict(dummy_state, verbose=0)
        print("Agent's brain is warmed up and ready.")

    def _build_model(self):
        """Builds a Dueling DQN model."""
        input_layer = Input(shape=(self.state_size,))
        
        # Shared layers
        shared = Dense(24, activation='relu')(input_layer)
        shared = Dense(24, activation='relu')(shared)
        
        # Value stream
        value_stream = Dense(16, activation='relu')(shared)
        value = Dense(1, activation='linear')(value_stream)
        
        # Advantage stream
        advantage_stream = Dense(16, activation='relu')(shared)
        advantage = Dense(self.action_size, activation='linear')(advantage_stream)
        
        # Combine value and advantage streams to get Q-values
        q_values = Lambda(lambda x: x[0] + (x[1] - K.mean(x[1], axis=1, keepdims=True)),
                          output_shape=(self.action_size,))([value, advantage])
        
        model = Model(inputs=input_layer, outputs=q_values)
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state, valid_actions=[0, 1]):
        """Chooses an action using epsilon-greedy policy with action masking."""
        if np.random.rand() <= self.epsilon:
            return random.choice(valid_actions)
        
        act_values = self.model.predict(state, verbose=0)[0]
        
        # Create a mask to only consider valid actions
        masked_act_values = np.full(self.action_size, -np.inf)
        masked_act_values[valid_actions] = act_values[valid_actions]
        
        return np.argmax(masked_act_values)

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                q_next = self.model.predict(next_state, verbose=0)[0]
                target = (reward + self.gamma * np.amax(q_next))
            target_f = self.model.predict(state, verbose=0)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)