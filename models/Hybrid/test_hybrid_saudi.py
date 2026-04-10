import gymnasium as gym
import numpy as np
import sinergym
import pandas as pd
import logging
import os
from sb3_contrib import RecurrentPPO 

# ==========================================
# 0. CONFIG & PATHS (KUALA LUMPUR TEST)
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)

# 1. Environment Settings
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
NEW_WEATHER = '/home/wansoon/Desktop/FYP_Metaverse/sinergym_source/sinergym/data/weather/Saudi.epw'
TIMESTEPS_TEST = 35040 

# 2. Path Setup
MODEL_DIR = "models/Hybrid/multi_seed_models"
MODEL_NAME = "hybrid_seed_10"


RESULT_DIR = "models/Hybrid/results_saudi"
CSV_NAME = "hybrid_results_saudi.csv"

# Ensure Output folder exists
os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. SMART ENERGY SHIELD (EXACT SAME)
# ==========================================
class SmartShield:
    def get_safety_action(self, current_temp):
        if current_temp > 25.8:
            return 24.0 
        elif current_temp < 23.2:
            return 28.0 
        return 26.0

# ==========================================
# 2. MAIN EXECUTION
# ==========================================
def main():
    print("="*60)
    print("🚀 TESTING HYBRID GENERALIZATION: SAUDI ARABRIC")
    print(f"   Weather File: {NEW_WEATHER}")
    print("="*60)
    
    # --- 1. SETUP ENVIRONMENT ---
    env = gym.make(ENV_NAME, weather_files=NEW_WEATHER)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    # --- 2. LOAD PRE-TRAINED MODEL ---
    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    
    try:
        # We explicitly load from the specific folder you gave me
        model = RecurrentPPO.load(model_path)
        print(f"✅ Loaded Brain from: {model_path}.zip")
    except:
        print(f"❌ CRITICAL ERROR: Model not found at {model_path}.zip")
        return

    # --- 3. RUN TEST ---
    shield = SmartShield()
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)
    obs, _ = env.reset()
    hits, steps, logs = 0, 0, []
    HEAT_FIXED = 23.25
    
    print(f"🔹 Running 1-Year Simulation ({TIMESTEPS_TEST} steps)...")
    print(f"   (Using LSTM States + Local Shield)")

    for i in range(TIMESTEPS_TEST):
        current_temp = obs[9]
        
        # --- HYBRID LOGIC ---
        # 1. Safety Shield
        if current_temp < 23.2 or current_temp > 25.8:
            safe_cooling = shield.get_safety_action(current_temp)
            action_vals = np.array([HEAT_FIXED, safe_cooling], dtype=np.float32)
            mode = "SHIELD_ACTIVE"
            _, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            
        else:
            # 2. Cloud AI
            action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            val = np.clip(action[0], -1.0, 1.0)
            ppo_cooling = 23.5 + (0.5 * (val + 1.0) * (28.0 - 23.5))
            action_vals = np.array([HEAT_FIXED, ppo_cooling], dtype=np.float32)
            mode = "LSTM_AI"

        obs, _, terminated, truncated, info = env.step(action_vals)
        episode_starts = terminated or truncated
        
        real_temp = obs[9]
        if 23.0 <= real_temp <= 26.0: 
            hits += 1
        steps += 1
        outdoor_temp = obs[3]
        logs.append([steps, real_temp, outdoor_temp, action_vals[1], obs[15], mode])
        
        if terminated or truncated: break
            
    # --- 4. SAVE RESULTS ---
    df = pd.DataFrame(logs, columns=['Step', 'Indoor_Temp', 'Outdoor_Temp', 'Setpoint', 'Power', 'Mode'])
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)

    final_acc = (hits / steps) * 100
    
    print("\n" + "═"*40)
    print(f"✅ Accuracy (Saudi Weather): {final_acc:.2f}%")
    print(f"📂 Results Saved:       {csv_path}")
    print("═"*40)
    
    env.close()

if __name__ == "__main__":
    main()
