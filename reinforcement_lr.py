import pandas as pd
import numpy as np
import gym # OpenAI Gym
from gym import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

dataset = pd.read_csv('data/dataset.csv', index_col='time', parse_dates=True)
dataset.drop(['active_power', 'voltage'], inplace=True, axis=1)
dataset['consumption'].fillna(method='ffill', inplace=True)
dataset['generation'].fillna(method='ffill', inplace=True)


class EnergyEnv(gym.Env):
    def __init__(self, generation, consumption, battery_capacity=10000):
        super(EnergyEnv, self).__init__()
        self.generation = generation
        self.consumption = consumption
        self.battery_capacity = battery_capacity
        self.current_step = 0
        self.battery_level = 0  # Initial battery level in kWh

        # Define action and observation space
        self.action_space = spaces.Discrete(3)  # 0: Do nothing, 1: Charge, 2: Discharge
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0]),
            high=np.array([battery_capacity, max(generation), max(consumption)]),
            dtype=np.float32
        )
        
    def seed(self, seed=None):
        self.np_random, seed = np.random.default_rng(seed), seed
        return [seed]
    
    def reset(self):
        self.current_step = 0
        self.battery_level = 0
        return self._get_state()
    
    def _get_state(self):
        return np.array([
            self.battery_level,
            self.generation[self.current_step],
            self.consumption[self.current_step]
        ], dtype=np.float32)
    
    def step(self, action):
        # Get current generation and consumption
        pv_gen = self.generation[self.current_step]
        load = self.consumption[self.current_step]
        
        # Perform action
        if action == 1:  # Charge
            excess_pv = pv_gen - load
            if excess_pv > 0:
                self.battery_level = min(self.battery_level + excess_pv, self.battery_capacity)
        elif action == 2:  # Discharge
            deficit = load - pv_gen
            if deficit > 0:
                discharge = min(deficit, self.battery_level)
                self.battery_level -= discharge
        
        # Calculate reward
        grid_import = max(0, load - pv_gen - self.battery_level)
        reward = -grid_import  # Negative reward for grid dependency
        
        # Update step
        self.current_step += 1
        done = self.current_step >= len(self.generation)
        next_state = self._get_state() if not done else None
        
        return next_state, reward, done, {}
    
    def render(self):
        print(f"Step: {self.current_step}, Battery Level: {self.battery_level:.2f} kWh")



generation = dataset['generation'].values
consumption = dataset['consumption'].values

# Initialize the environment
env = EnergyEnv(generation, consumption)
vec_env = make_vec_env(lambda: env, n_envs=1)

# Initialize the PPO agent
model = PPO("MlpPolicy", vec_env, verbose=1)

# Train the agent
model.learn(total_timesteps=100)

# # Save the model
# model.save("energy_agent")


# # Load the trained agent
# model = PPO.load("energy_agent")

# Reset the environment
state = env.reset()
done = False

while not done:
    action, _ = model.predict(state)
    state, reward, done, _ = env.step(action)
    env.render()


import matplotlib.pyplot as plt
import numpy as np

# Simulate the environment for 1 week (assuming hourly data)
env.reset()
states, actions, rewards, battery_levels, grid_imports, pv_generation, consumption = [], [], [], [], [], [], []

done = False
while not done:
    state = env._get_state()
    action, _ = model.predict(state)
    next_state, reward, done, _ = env.step(action)
    
    # Save data for visualization
    states.append(state)
    actions.append(action)
    rewards.append(reward)
    battery_levels.append(env.battery_level)
    grid_imports.append(max(0, state[2] - state[1] - env.battery_level))  # Grid import
    pv_generation.append(state[1])
    consumption.append(state[2])

# Convert lists to numpy arrays for easier plotting
battery_levels = np.array(battery_levels)
grid_imports = np.array(grid_imports)
pv_generation = np.array(pv_generation)
consumption = np.array(consumption)

# Generate time labels for a week
time_labels = [f"Day {i//24+1}, Hour {i%24}" for i in range(len(battery_levels))]

# Plot the results
plt.figure(figsize=(14, 10))

# PV Generation and Consumption
plt.subplot(3, 1, 1)
plt.plot(pv_generation, label='PV Generation (kW)', color='orange')
plt.plot(consumption, label='Consumption (kW)', color='blue')
plt.title('PV Generation and Consumption')
plt.ylabel('Power (kW)')
plt.legend()

# Battery Level
plt.subplot(3, 1, 2)
plt.plot(battery_levels, label='Battery Level (Wh)', color='green')
plt.title('Battery Level')
plt.ylabel('Energy (Wh)')
plt.legend()


plt.subplot(3, 1, 3)
plt.plot(grid_imports, label='Grid Import (W)', color='red')
plt.title('Grid Import')
plt.ylabel('Power (kW)')
plt.xlabel('Time')
plt.legend()

plt.xticks(ticks=range(0, len(time_labels), 24), labels=[time_labels[i] for i in range(0, len(time_labels), 24)], rotation=45)

plt.tight_layout()
plt.show()
plt.close()



pv_self_consumption = np.sum(pv_generation - grid_imports) / np.sum(pv_generation) * 100

    
print(f"pv self consumption: {pv_self_consumption:.2f}%")