import gymnasium as gym
import numpy as np
import sinergym
import logging
import pandas as pd
import os
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

# ==========================================
# 0. CONFIG & PATHS (KUALA LUMPUR TEST)
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)

# 1. Environment Settings
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
# CRITICAL CHANGE: Force Sinergym to use the Kuala Lumpur Weather File
NEW_WEATHER = 'KualaLumpur.epw' 
TIMESTEPS_TEST = 35040

# 2. Path Setup
# Load the ORIGINAL model (Trained on New York)
MODEL_DIR = "models/PPO/saved_models"
MODEL_NAME = "ppo_final_fixed"

# Save results to a NEW "Kuala Lumpur" folder
RESULT_DIR = "models/PPO/results_kl"
CSV_NAME = "ppo_final_results_kl.csv"

# Ensure folders exist
os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. PPO WRAPPER (EXACT SAME AS TRAINING)
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

        # Reward Logic (Maintained for consistency)
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
# 2. MAIN EXECUTION
# ==========================================
def main():
    print("="*60)
    print("🚀 TESTING PPO GENERALIZATION: KUALA LUMPUR")
    print(f"   Weather File: {NEW_WEATHER}")
    print("="*60)
    
    # --- 1. SETUP ENVIRONMENT ---
    # We pass 'weather_files' (plural) to override the default weather
    env = gym.make(ENV_NAME, weather_files=NEW_WEATHER) 
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    env = SafePPOWrapper(env)
    
    # --- 2. LOAD PRE-TRAINED MODEL ---
    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    
    if os.path.exists(model_path + ".zip"):
        print(f"🔹 Loading Model: {model_path}.zip")
        model = PPO.load(model_path)
    else:
        print(f"❌ CRITICAL ERROR: Model not found at {model_path}.zip")
        return

    # --- 3. RUN TEST ---
    obs, _ = env.reset()
    hits, steps, logs = 0, 0, []
    
    print(f"🔹 Running 1-Year Simulation in KL...")

    for i in range(TIMESTEPS_TEST):
        # AI Predicts (Brain thinks it's in New York)
        action, _ = model.predict(obs)
        
        # Environment Responds (Weather is actually KL)
        obs, _, terminated, truncated, info = env.step(action)
        
        if 23.0 <= info['real_temp'] <= 26.0: 
            hits += 1
        steps += 1
        logs.append([steps, info['real_temp'], info['cooling_setpoint'], obs[15]])
        
        if terminated or truncated: break
            
    # --- 4. SAVE RESULTS ---
    df = pd.DataFrame(logs, columns=['Step', 'Temp', 'Setpoint', 'Power'])
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)
    
    final_acc = (hits / steps) * 100
    
    print("\n" + "═"*40)
    print(f"✅ Accuracy (KL Weather): {final_acc:.2f}%")
    print(f"📂 Results Saved:       {csv_path}")
    print("═"*40)
    env.close()

if __name__ == "__main__":
    main()
