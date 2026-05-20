import sys
import gymnasium as gym
import sinergym
import torch
import numpy as np
import pandas as pd
import logging
import os
from sb3_contrib import RecurrentPPO

# ==========================================
# 0. CONFIG & PATHS
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
SAUDI_WEATHER_PATH = '/home/wansoon/Desktop/FYP_Metaverse/sinergym_source/sinergym/data/weather/Saudi.epw' 
TIMESTEPS_TEST = 35040 

MODEL_DIR = "models/Hybrid/saved_models"  
RESULT_DIR = "models/Hybrid/results_saudi"
MODEL_NAME = "ppo_lstm"
CSV_NAME = "hybrid_results_saudi.csv"

os.makedirs(RESULT_DIR, exist_ok=True)
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
# 2. MAIN SINGLE-RUN TEST
# ==========================================
def main():
    print("="*60)
    print("🚀 RUNNING SAUDI-SPECIALIST HYBRID TEST")
    print("="*60)
    
    env = gym.make(ENV_NAME, weather_files=SAUDI_WEATHER_PATH)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    try:
        model = RecurrentPPO.load(model_path)
        print(f"✅ Loaded Brain from: {model_path}.zip")
    except:
         print(f"❌ Error: Model not found at {model_path}.zip")
         return

    shield = SmartShield()
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)
    obs, _ = env.reset()
    
    total_energy_kwh = 0.0
    comfort_violations = 0
    hits = 0
    shield_activations = 0
    logs = []
    
    for step in range(TIMESTEPS_TEST):
        current_temp = obs[9]  
        current_power_w = obs[15] 
        
        if current_temp < 23.2 or current_temp > 25.8:
            # SHIELD ACTIVE
            safe_cooling = shield.get_safety_action(current_temp)
            action_vals = np.array([23.25, safe_cooling], dtype=np.float32)
            mode = "SHIELD_ACTIVE"
            shield_activations += 1
            _, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
        else:
            # AI ACTIVE (Synchronized 2D Decoding)
            action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            val_heat = np.clip(action[0], -1.0, 1.0)
            val_cool = np.clip(action[1], -1.0, 1.0)
            
            heating_setpoint = 12.0 + (0.5 * (val_heat + 1.0) * (23.25 - 12.0))
            cooling_setpoint = 23.5 + (0.5 * (val_cool + 1.0) * (30.0 - 23.5))
            
            action_vals = np.array([heating_setpoint, cooling_setpoint], dtype=np.float32)
            mode = "LSTM_AI"

        obs, _, terminated, truncated, info = env.step(action_vals)
        episode_starts = terminated or truncated
        
        real_temp = obs[9] 
        
        energy_kwh = (current_power_w * (900 / 3600)) / 1000.0 
        total_energy_kwh += energy_kwh
        
        if 23.0 <= real_temp <= 26.0: 
            hits += 1
        else:
            comfort_violations += 1

        logs.append([step, real_temp, action_vals[1], obs[15], mode])
        
        if step % 5000 == 0 and step > 0:
            print(f"   ...Step {step}/{TIMESTEPS_TEST} | Temp: {real_temp:.2f}°C | Mode: {mode}", flush=True)

        if terminated or truncated: break
            
    final_acc = (hits / TIMESTEPS_TEST) * 100 
    shield_rate = (shield_activations / TIMESTEPS_TEST) * 100
    
    df = pd.DataFrame(logs, columns=['Step', 'Temp', 'Setpoint', 'Power', 'Mode'])
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)

    print("\n" + "═"*50)
    print(f"✅ Accuracy (Hits):    {final_acc:.2f}%") 
    print(f"✅ Total Energy:       {total_energy_kwh:.1f} kWh")
    print(f"✅ Violations:         {comfort_violations}")
    print(f"🛡️ Shield Active:      {shield_rate:.2f}% of the year")
    print(f"📂 Step-by-Step CSV:   {csv_path}")
    print("═"*50)
    
    env.close()

if __name__ == "__main__":
    main()
