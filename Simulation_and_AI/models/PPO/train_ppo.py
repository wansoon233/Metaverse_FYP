import gymnasium as gym
import numpy as np
import sinergym
import logging
import pandas as pd
import os
from stable_baselines3 import PPO
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
MODEL_DIR = "models/PPO/saved_models"
RESULT_DIR = "models/PPO/results"
MODEL_NAME = "ppo_final_fixed"
CSV_NAME = "ppo_final_results.csv"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. PPO WRAPPER
# ==========================================
class SafePPOWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        self.HEAT_FIXED = 23.25      
        self.COOL_MIN = 23.5         
        self.COOL_MAX = 28.0         

    def step(self, action):
        val = np.clip(action[0], -1.0, 1.0)
        cooling_setpoint = self.COOL_MIN + (0.5 * (val + 1.0) * (self.COOL_MAX - self.COOL_MIN))
        dual_action = np.array([self.HEAT_FIXED, cooling_setpoint], dtype=np.float32)
        obs, _, terminated, truncated, info = self.env.step(dual_action)
        
        temp_c = obs[9]        
        energy_power = obs[15] 

        if 23.0 <= temp_c <= 26.0:
            dist = abs(temp_c - 24.5)
            score = 2.0 + (1.0 - dist)
        else:
            diff = min(abs(23.0 - temp_c), abs(temp_c - 26.0))
            score = -(diff * 5.0)
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
            print(f"   [PPO] Training Step {self.n_calls}/{TIMESTEPS_TRAIN}")
        return True

# ==========================================
# 3. MAIN
# ==========================================
def main():
    print("="*60)
    print("🚀 TRAINING PPO (Organized Output)")
    print("="*60)
    
    # --- TRAIN ---
    env = gym.make(ENV_NAME) 
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    env = SafePPOWrapper(env)
    env = Monitor(env)

    model = PPO("MlpPolicy", env, verbose=0, learning_rate=0.0003, n_steps=2048, batch_size=64, ent_coef=0.01)
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
    test_env = SafePPOWrapper(test_env)
    obs, _ = test_env.reset()
    hits, steps, logs = 0, 0, []
    
    for i in range(TIMESTEPS_TEST):
        action, _ = model.predict(obs)
        obs, _, terminated, truncated, info = test_env.step(action)
        if 23.0 <= info['real_temp'] <= 26.0: hits += 1
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
