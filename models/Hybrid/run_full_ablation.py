import gymnasium as gym
import numpy as np
import sinergym
import pandas as pd
import logging
import os
from sb3_contrib import RecurrentPPO
from stable_baselines3 import PPO

logging.getLogger('sinergym').setLevel(logging.WARNING)

# ==========================================
# 0. CONFIG & PATHS
# ==========================================
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
KL_WEATHER_PATH = '/home/wansoon/Desktop/FYP_Metaverse/sinergym_source/sinergym/data/weather/KualaLumpur.epw' 
TIMESTEPS_TEST = 35040 

PPO_MODEL_PATH = "/home/wansoon/Desktop/FYP_Metaverse/models/PPO/saved_models/ppo_final_fixed.zip"
LSTM_MODEL_PATH = "/home/wansoon/Desktop/FYP_Metaverse/models/Hybrid/saved_models/ppo_lstm.zip"
RESULTS_CSV_PATH = "/home/wansoon/Desktop/FYP_Metaverse/models/Hybrid/results/ablation_results.csv"

print("="*70)
print("🔬 FULL 5-PART ABLATION STUDY")
print("="*70)

try:
    model_ppo = PPO.load(PPO_MODEL_PATH)
    model_lstm = RecurrentPPO.load(LSTM_MODEL_PATH)
except Exception as e:
    print(f"❌ Failed to load a model! Error: {e}")
    exit()

def run_ablation(config_name, ai_type, use_shield):
    print(f"\n⏳ Running Config: {config_name}")
    
    env = gym.make(ENV_NAME, weather_files=KL_WEATHER_PATH)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    obs, _ = env.reset(seed=10)
    
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)
    total_energy = 0.0
    violations = 0
    
    for step in range(TIMESTEPS_TEST):
        current_temp = obs[9]
        current_power_w = obs[15]
        
        # --- 1. SHIELD / RBC OVERRIDE LOGIC ---
        if use_shield and (current_temp < 23.2 or current_temp > 25.8):
            safe_cooling = 24.0 if current_temp > 25.8 else 28.0
            action_vals = np.array([23.25, safe_cooling], dtype=np.float32)
            
            # Keep LSTM memory updating silently in the background
            if ai_type == "LSTM":
                _, lstm_states = model_lstm.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
                
        # --- 2. PURE RBC BASELINE (NO AI) ---
        elif ai_type == "RBC":
            # Standard thermostat: Heat at 22, Cool at 25
            action_vals = np.array([22.0, 25.0], dtype=np.float32)

        # --- 3. STANDARD PPO LOGIC ---
        elif ai_type == "PPO":
            action, _ = model_ppo.predict(obs, deterministic=True)
            val = np.clip(action[0], -1.0, 1.0)
            heating_setpoint = 23.25 
            cooling_setpoint = 23.5 + (0.5 * (val + 1.0) * (28.0 - 23.5))
            action_vals = np.array([heating_setpoint, cooling_setpoint], dtype=np.float32)

        # --- 4. LSTM-PPO LOGIC ---
        elif ai_type == "LSTM":
            action, lstm_states = model_lstm.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            val_heat = np.clip(action[0], -1.0, 1.0)
            val_cool = np.clip(action[1], -1.0, 1.0)
            heating_setpoint = 12.0 + (0.5 * (val_heat + 1.0) * (23.25 - 12.0))
            cooling_setpoint = 23.5 + (0.5 * (val_cool + 1.0) * (30.0 - 23.5))
            action_vals = np.array([heating_setpoint, cooling_setpoint], dtype=np.float32)

        # Execute Action
        obs, _, terminated, truncated, _ = env.step(action_vals)
        episode_starts = terminated or truncated
        
        # Track Metrics
        energy_kwh = (current_power_w * (900 / 3600)) / 1000.0 
        total_energy += energy_kwh
        if obs[9] < 23.0 or obs[9] > 26.0: 
            violations += 1
            
        if terminated or truncated: break
            
    env.close()
    return total_energy, violations

# ==========================================
# EXECUTE 5-PART ABLATION STUDY
# ==========================================
results = []

# 1. RBC Only (Baseline)
e0, v0 = run_ablation("1. Pure RBC", ai_type="RBC", use_shield=True)
results.append(["Pure RBC", e0, v0])

# 2. PPO Only
e1, v1 = run_ablation("2. Standard PPO", ai_type="PPO", use_shield=False)
results.append(["Standard PPO", e1, v1])

# 3. PPO + Shield
e2, v2 = run_ablation("3. PPO + Shield", ai_type="PPO", use_shield=True)
results.append(["PPO + Shield", e2, v2])

# 4. LSTM-PPO
e3, v3 = run_ablation("4. LSTM-PPO", ai_type="LSTM", use_shield=False)
results.append(["LSTM-PPO", e3, v3])

# 5. Full Hybrid (LSTM-PPO + Shield)
e4, v4 = run_ablation("5. Full Hybrid", ai_type="LSTM", use_shield=True)
results.append(["Full Hybrid", e4, v4])

print("\n" + "="*70)
print(f"{'Configuration':<18} | {'Energy (kWh)':<12} | {'Violations'}")
print("-" * 70)
for r in results:
    print(f"{r[0]:<18} | {r[1]:<12.1f} | {r[2]}")
print("="*70)

os.makedirs(os.path.dirname(RESULTS_CSV_PATH), exist_ok=True)
df = pd.DataFrame(results, columns=["Configuration", "Energy (kWh)", "Violations"])
df.to_csv(RESULTS_CSV_PATH, index=False)
print(f"\n✅ Results successfully saved to: {RESULTS_CSV_PATH}")
