import gymnasium as gym
import numpy as np
import sinergym
import pandas as pd
import logging
import os
from sb3_contrib import RecurrentPPO 

# ==========================================
# 0. CONFIG & PATHS
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
TIMESTEPS_TEST = 35040 

# --- NEW PATH SETUP ---
MODEL_DIR = "models/Hybrid/saved_models"  
RESULT_DIR = "models/Hybrid/results"
MODEL_NAME = "ppo_lstm_fast"
CSV_NAME = "hybrid_lstm_results.csv"

# Ensure Output folder exists
os.makedirs(RESULT_DIR, exist_ok=True)
# Ensure Input folder exists (so we don't crash if you forgot to make it)
os.makedirs(MODEL_DIR, exist_ok=True)

# ==========================================
# 1. SMART ENERGY SHIELD
# ==========================================
class SmartShield:
    def get_safety_action(self, current_temp):
        if current_temp > 25.8:
            return 24.0 
        elif current_temp < 23.2:
            return 28.0 
        return 26.0

# ==========================================
# 2. MAIN
# ==========================================
def main():
    print("="*60)
    print("🚀 RUNNING HYBRID (Deterministic & Organized)")
    print("="*60)
    
    env = gym.make(ENV_NAME)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    # LOAD MODEL (Look in specific folder first, then root as backup)
    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    
    try:
        model = RecurrentPPO.load(model_path)
        print(f"✅ Loaded Brain from: {model_path}.zip")
    except:
        print(f"⚠️ Could not find model at {model_path}.zip")
        print(f"   Trying current folder...")
        try:
            model = RecurrentPPO.load(MODEL_NAME)
            print(f"✅ Loaded Brain from local folder.")
        except:
             print("❌ Error: Model not found anywhere!")
             return

    shield = SmartShield()
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)
    obs, _ = env.reset()
    hits, steps, logs = 0, 0, []
    HEAT_FIXED = 23.25
    
    for i in range(TIMESTEPS_TEST):
        current_temp = obs[9]
        
        if current_temp < 23.2 or current_temp > 25.8:
            safe_cooling = shield.get_safety_action(current_temp)
            action_vals = np.array([HEAT_FIXED, safe_cooling], dtype=np.float32)
            mode = "SHIELD_ACTIVE"
            _, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
        else:
            action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            val = np.clip(action[0], -1.0, 1.0)
            ppo_cooling = 23.5 + (0.5 * (val + 1.0) * (28.0 - 23.5))
            action_vals = np.array([HEAT_FIXED, ppo_cooling], dtype=np.float32)
            mode = "LSTM_AI"

        obs, _, terminated, truncated, info = env.step(action_vals)
        episode_starts = terminated or truncated
        
        real_temp = obs[9]
        if 23.0 <= real_temp <= 26.0: hits += 1
        steps += 1
        logs.append([steps, real_temp, action_vals[1], obs[15], mode])
        if terminated or truncated: break
            
    final_acc = (hits / steps) * 100
    
    # SAVE RESULTS
    df = pd.DataFrame(logs, columns=['Step', 'Temp', 'Setpoint', 'Power', 'Mode'])
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)

    print("\n" + "═"*40)
    print(f"✅ Accuracy:      {final_acc:.2f}%")
    print(f"📂 Results:       {csv_path}")
    print("═"*40)
    
    env.close()

if __name__ == "__main__":
    main()
