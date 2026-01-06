import gymnasium as gym
import numpy as np
import sinergym
import pandas as pd
import logging
import os

# ==========================================
# 0. CONFIG & PATHS (TOKYO TEST)
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)

ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
NEW_WEATHER = 'JPN_Tokyo.Hyakuri.477150_IWEC.epw' 
TIMESTEPS_TEST = 35040 

RESULT_DIR = "models/RBC/results_tokyo"
CSV_NAME = "rbc_results_tokyo.csv"

os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. RBC LOGIC
# ==========================================
def get_rbc_action(current_temp):
    if current_temp > 25.0:
        return 24.0
    elif current_temp < 23.0:
        return 28.0
    else:
        return 26.0

# ==========================================
# 2. MAIN
# ==========================================
def main():
    print("="*60)
    print("🚀 TESTING RBC GENERALIZATION: TOKYO")
    print(f"   Weather: {NEW_WEATHER}")
    print("="*60)
    
    env = gym.make(ENV_NAME, weather_files=NEW_WEATHER)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    obs, _ = env.reset()
    hits, steps, logs = 0, 0, []
    HEAT_FIXED = 23.25
    
    for i in range(TIMESTEPS_TEST):
        current_temp = obs[9]
        cooling_setpoint = get_rbc_action(current_temp)
        action_vals = np.array([HEAT_FIXED, cooling_setpoint], dtype=np.float32)
        obs, _, terminated, truncated, info = env.step(action_vals)
        
        real_temp = obs[9]
        if 23.0 <= real_temp <= 26.0: hits += 1
        steps += 1
        logs.append([steps, real_temp, cooling_setpoint, obs[15]])
        if terminated or truncated: break
            
    df = pd.DataFrame(logs, columns=['Step', 'Temp', 'Setpoint', 'Power'])
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)
    
    final_acc = (hits / steps) * 100
    total_energy_kwh = (df['Power'].sum() * 0.25) / 1000.0

    print("\n" + "═"*40)
    print(f"✅ Accuracy (Tokyo): {final_acc:.2f}%")
    print(f"⚡ Energy: {total_energy_kwh:.2f} kWh")
    print(f"📂 Results: {csv_path}")
    print("═"*40)
    env.close()

if __name__ == "__main__":
    main()
