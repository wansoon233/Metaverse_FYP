import gymnasium as gym
import numpy as np
import sinergym
import logging
import pandas as pd
import os
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

# ==========================================
# 0. CONFIG & PATHS
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1' 
TIMESTEPS_TRAIN = 200000 
TIMESTEPS_TEST = 35040

# --- NEW PATH SETUP ---
MODEL_DIR = "models/DQN/saved_models"
RESULT_DIR = "models/DQN/results"
MODEL_NAME = "dqn_smart_final"
CSV_NAME = "dqn_results_final.csv"

# Ensure folders exist
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. SMART DQN WRAPPER
# ==========================================
class SmartDQNWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.n_actions = 20
        self.action_space = gym.spaces.Discrete(self.n_actions)
        self.setpoint_map = np.linspace(24.0, 28.0, self.n_actions)
        self.HEAT_FIXED = 23.25      

    def step(self, action):
        cooling_setpoint = self.setpoint_map[int(action)]
        dual_action = np.array([self.HEAT_FIXED, cooling_setpoint], dtype=np.float32)
        obs, _, terminated, truncated, info = self.env.step(dual_action)
        
        temp_c = obs[9]        
        energy_power = obs[15] 

        # Reward
        if 23.0 <= temp_c <= 26.0:
            dist = abs(temp_c - 24.5)
            score = 2.0 + (2.0 * (1.0 - dist)) 
        else:
            diff = min(abs(23.0 - temp_c), abs(temp_c - 26.0))
            score = -(diff * 10.0)

        energy_score = -1.0 * (energy_power / 10000.0)
        info['cooling_setpoint'] = cooling_setpoint
        info['real_temp'] = temp_c 
        return obs, (score + energy_score), terminated, truncated, info

# ==========================================
# 2. LOGGER
# ==========================================
class CleanLogger(BaseCallback):
    def _on_step(self) -> bool:
        if self.n_calls % 10000 == 0:
            print(f"   [Smart-DQN] Training Step {self.n_calls}/{TIMESTEPS_TRAIN}")
        return True

# ==========================================
# 3. MAIN
# ==========================================
def main():
    print("="*60)
    print("🚀 TRAINING SMART DQN (Organized Output)")
    print("="*60)
    
    # --- TRAIN ---
    env = gym.make(ENV_NAME) 
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    env = SmartDQNWrapper(env)
    env = Monitor(env)

    policy_kwargs = dict(net_arch=[128, 128]) 
    model = DQN("MlpPolicy", env, verbose=0, learning_rate=0.0005, buffer_size=100000, 
                learning_starts=5000, batch_size=128, gamma=0.99, exploration_fraction=0.2, 
                exploration_final_eps=0.02, policy_kwargs=policy_kwargs)

    print(f"🔹 Training for {TIMESTEPS_TRAIN} steps...")
    model.learn(total_timesteps=TIMESTEPS_TRAIN, callback=CleanLogger())
    
    # SAVE TO FOLDER
    save_path = os.path.join(MODEL_DIR, MODEL_NAME)
    model.save(save_path)
    print(f"✅ Model Saved: {save_path}.zip")
    env.close()

    # --- TEST ---
    print("\n📝 RUNNING EVALUATION")
    test_env = gym.make(ENV_NAME)
    try: test_env.unwrapped.simulator.display_progress = False
    except: pass
    
    test_env = SmartDQNWrapper(test_env)
    obs, _ = test_env.reset()
    hits, steps, logs = 0, 0, []
    
    for i in range(TIMESTEPS_TEST):
        action, _ = model.predict(obs)
        obs, _, terminated, truncated, info = test_env.step(action)
        
        if 23.0 <= info['real_temp'] <= 26.0:
            hits += 1
        steps += 1
        logs.append([steps, info['real_temp'], info['cooling_setpoint'], obs[15]])
        if terminated or truncated: break
            
    # SAVE RESULTS
    df = pd.DataFrame(logs, columns=['Step', 'Temp', 'Setpoint', 'Power'])
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)
    
    final_acc = (hits / steps) * 100
    print("\n" + "═"*40)
    print(f"✅ Accuracy:      {final_acc:.2f}%")
    print(f"📂 Results:       {csv_path}")
    print("═"*40)
    test_env.close()

if __name__ == "__main__":
    main()
