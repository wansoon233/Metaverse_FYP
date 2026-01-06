import gymnasium as gym
import numpy as np
import sinergym
import logging
import pandas as pd
import os
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

# ==========================================
# 0. CONFIG & PATHS (TOKYO TEST)
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)

ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
NEW_WEATHER = 'JPN_Tokyo.Hyakuri.477150_IWEC.epw' 
TIMESTEPS_TEST = 35040

# Load NY Model
MODEL_DIR = "models/PPO/saved_models"
MODEL_NAME = "ppo_final_fixed"

# Save to Tokyo Results
RESULT_DIR = "models/PPO/results_tokyo"
CSV_NAME = "ppo_final_results_tokyo.csv"

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
# 2. MAIN
# ==========================================
def main():
    print("="*60)
    print("🚀 TESTING PPO GENERALIZATION: TOKYO")
    print(f"   Weather: {NEW_WEATHER}")
    print("="*60)
    
    env = gym.make(ENV_NAME, weather_files=NEW_WEATHER) 
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    env = SafePPOWrapper(env)
    
    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    if os.path.exists(model_path + ".zip"):
        print(f"🔹 Loading NY Model: {model_path}.zip")
        model = PPO.load(model_path)
    else:
        print(f"❌ Model not found at {model_path}.zip")
        return

    obs, _ = env.reset()
    hits, steps, logs = 0, 0, []
    
    for i in range(TIMESTEPS_TEST):
        action, _ = model.predict(obs)
        obs, _, terminated, truncated, info = env.step(action)
        if 23.0 <= info['real_temp'] <= 26.0: hits += 1
        steps += 1
        logs.append([steps, info['real_temp'], info['cooling_setpoint'], obs[15]])
        if terminated or truncated: break
            
    df = pd.DataFrame(logs, columns=['Step', 'Temp', 'Setpoint', 'Power'])
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)
    
    final_acc = (hits / steps) * 100
    print("\n" + "═"*40)
    print(f"✅ Accuracy (Tokyo): {final_acc:.2f}%")
    print(f"📂 Results: {csv_path}")
    print("═"*40)
    env.close()

if __name__ == "__main__":
    main()
