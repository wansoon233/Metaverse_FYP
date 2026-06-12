import gymnasium as gym
import numpy as np
import sinergym
import pandas as pd
import logging
import os

# ==========================================
# 0. CONFIG & PATHS (KUALA LUMPUR TEST)
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)

# 1. Environment Settings
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
# CRITICAL CHANGE: Force Sinergym to use the Kuala Lumpur Weather File
NEW_WEATHER = 'KualaLumpur.epw' 
TIMESTEPS_TEST = 35040 # Exact 1 Year

# 2. Path Setup
RESULT_DIR = "models/RBC/results_kl"
CSV_NAME = "rbc_results_kl.csv"

# Ensure Output folder exists
os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. RBC LOGIC (EXACT SAME)
# ==========================================
def get_rbc_action(current_temp):
    # Simple Logic (Maintained for consistency):
    # If Hot (>25.0) -> Cool Hard (24.0)
    # If Good (23-25) -> Relax (26.0)
    # If Cold (<23.0) -> Stop Cooling (28.0)
    
    if current_temp > 25.0:
        return 24.0
    elif current_temp < 23.0:
        return 28.0
    else:
        return 26.0

# ==========================================
# 2. MAIN EXECUTION
# ==========================================
def main():
    print("="*60)
    print("🚀 TESTING RBC GENERALIZATION: KUALA LUMPUR")
    print(f"   Weather File: {NEW_WEATHER}")
    print("="*60)
    
    # --- 1. SETUP ENVIRONMENT ---
    # We pass 'weather_files' (plural) to override the default weather
    env = gym.make(ENV_NAME, weather_files=NEW_WEATHER)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    obs, _ = env.reset()
    hits, steps, logs = 0, 0, []
    
    # CRITICAL FIX: 23.25 (Matches your AI models)
    HEAT_FIXED = 23.25
    
    print(f"🔹 Running 1-Year Simulation ({TIMESTEPS_TEST} steps)...")
    
    for i in range(TIMESTEPS_TEST):
        current_temp = obs[9]
        
        # Calculate Action
        cooling_setpoint = get_rbc_action(current_temp)
        action_vals = np.array([HEAT_FIXED, cooling_setpoint], dtype=np.float32)
        
        # Step
        obs, _, terminated, truncated, info = env.step(action_vals)
        
        real_temp = obs[9]
        if 23.0 <= real_temp <= 26.0:
            hits += 1
            
        steps += 1
        logs.append([steps, real_temp, cooling_setpoint, obs[15]])
        
        if terminated or truncated:
            break
            
    # --- SAVE RESULTS ---
    df = pd.DataFrame(logs, columns=['Step', 'Temp', 'Setpoint', 'Power'])
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)
    
    # --- METRICS ---
    final_acc = (hits / steps) * 100
    total_energy_kwh = (df['Power'].sum() * 0.25) / 1000.0
    avg_temp = df['Temp'].mean()

    print("\n" + "═"*40)
    print("        🏆 RBC RESULTS (KUALA LUMPUR)")
    print("═"*40)
    print(f"✅ Accuracy:       {final_acc:.2f}%")
    print(f"⚡ Total Energy:   {total_energy_kwh:.2f} kWh")
    print(f"🌡️  Avg Temp:       {avg_temp:.2f} °C")
    print(f"📂 Results:        {csv_path}")
    print("═"*40)
    
    env.close()

if __name__ == "__main__":
    main()
