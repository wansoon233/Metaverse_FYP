import gymnasium as gym
import numpy as np
import sinergym
import pandas as pd
import logging
import os

# ==========================================
# 0. CONFIG & PATHS
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
TIMESTEPS_TEST = 35040 

# --- NEW PATH SETUP ---
RESULT_DIR = "models/RBC/results"
CSV_NAME = "rbc_results.csv"

# Ensure Output folder exists
os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. RBC LOGIC (Rule Based Control)
# ==========================================
def get_rbc_action(current_temp):
    # Simple Logic:
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
    print("🚀 RUNNING RBC CONTROLLER (Organized Output)")
    print("="*60)
    
    env = gym.make(ENV_NAME)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    obs, _ = env.reset()
    hits, steps, logs = 0, 0, []
    
    # CRITICAL FIX: 23.25 (Matches your AI models)
    HEAT_FIXED = 23.25
    
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
            
    final_acc = (hits / steps) * 100
    
    # SAVE RESULTS
    df = pd.DataFrame(logs, columns=['Step', 'Temp', 'Setpoint', 'Power'])
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)
    
    # METRICS
    total_energy_kwh = (df['Power'].sum() * 0.25) / 1000.0
    avg_temp = df['Temp'].mean()

    print("\n" + "═"*40)
    print("       🏆 RBC RESULTS")
    print("═"*40)
    print(f"✅ Accuracy:      {final_acc:.2f}%")
    print(f"⚡ Total Energy:  {total_energy_kwh:.2f} kWh")
    print(f"🌡️  Avg Temp:      {avg_temp:.2f} °C")
    print(f"📂 Results:       {csv_path}")
    print("═"*40)
    
    env.close()

if __name__ == "__main__":
    main()
