import gymnasium as gym
import numpy as np
import sinergym
import logging
import pandas as pd
import os
from stable_baselines3 import DQN
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
# Load the ORIGINAL model (Trained on New York/Mixed)
MODEL_DIR = "models/DQN/saved_models"
MODEL_NAME = "dqn_smart_final"

# Save results to a NEW "Kuala Lumpur" folder
RESULT_DIR = "models/DQN/results_kl"
CSV_NAME = "dqn_results_kl.csv"

# Ensure folders exist
os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. SMART DQN WRAPPER (EXACT SAME AS TRAINING)
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

        # Reward Logic (Maintained for state consistency)
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
# 2. MAIN EXECUTION
# ==========================================
def main():
    print("="*60)
    print("🚀 TESTING DQN GENERALIZATION: KUALA LUMPUR")
    print(f"   Weather File: {NEW_WEATHER}")
    print("="*60)
    
    # --- 1. SETUP ENVIRONMENT ---
    # We pass 'weather_file' to override the default (New York) weather
    env = gym.make(ENV_NAME, weather_files=NEW_WEATHER)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    env = SmartDQNWrapper(env)
    
    # --- 2. LOAD PRE-TRAINED MODEL ---
    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    
    if os.path.exists(model_path + ".zip"):
        print(f"🔹 Loading Model: {model_path}.zip")
        model = DQN.load(model_path)
    else:
        print(f"❌ CRITICAL ERROR: Model not found at {model_path}.zip")
        print("   Please run the Training script first!")
        return

    # --- 3. RUN TEST ---
    print(f"🔹 Running 1-Year Simulation ({TIMESTEPS_TEST} steps)...")
    
    obs, _ = env.reset()
    hits, steps, logs = 0, 0, []
    
    for i in range(TIMESTEPS_TEST):
        # Predict using the loaded brain
        action, _ = model.predict(obs)
        
        # Step environment
        obs, _, terminated, truncated, info = env.step(action)
        
        # Log Stats
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
