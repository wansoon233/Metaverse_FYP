import gymnasium as gym
import numpy as np
import sinergym
import pandas as pd
import logging
import os
from sb3_contrib import RecurrentPPO 

logging.getLogger('sinergym').setLevel(logging.WARNING)

# ==========================================
# 0. CONFIG 
# ==========================================
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
KL_WEATHER_PATH = '/home/wansoon/Desktop/FYP_Metaverse/sinergym_source/sinergym/data/weather/KualaLumpur.epw' 
TIMESTEPS_TEST = 35040 
MODEL_PATH = "/home/wansoon/Desktop/FYP_Metaverse/models/Hybrid/saved_models/ppo_lstm.zip"

print("="*60)
print("🔬 FULL 4-PART ABLATION STUDY (KL WEATHER)")
print("="*60)

try:
    model = RecurrentPPO.load(MODEL_PATH)
except:
    print(f"❌ Failed to load {MODEL_PATH}. Check your path!")
    exit()

def run_ablation(config_name, use_lstm, use_shield):
    print(f"\n⏳ Running Config: {config_name}")
    print(f"   LSTM (Memory): {'✅ YES' if use_lstm else '❌ NO'}")
    print(f"   RBC (Shield):  {'✅ YES' if use_shield else '❌ NO'}")
    
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
        
        if use_shield and (current_temp < 23.2 or current_temp > 25.8):
            safe_cooling = 24.0 if current_temp > 25.8 else 28.0
            action_vals = np.array([23.25, safe_cooling], dtype=np.float32)
            if use_lstm:
                _, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
        else:
            state_in = lstm_states if use_lstm else None
            start_in = episode_starts if use_lstm else np.ones((1,), dtype=bool)
            
            action, lstm_states = model.predict(obs, state=state_in, episode_start=start_in, deterministic=True)
            
            val_heat = np.clip(action[0], -1.0, 1.0)
            val_cool = np.clip(action[1], -1.0, 1.0)
            
            heating_setpoint = 12.0 + (0.5 * (val_heat + 1.0) * (23.25 - 12.0))
            cooling_setpoint = 23.5 + (0.5 * (val_cool + 1.0) * (30.0 - 23.5))
            
            action_vals = np.array([heating_setpoint, cooling_setpoint], dtype=np.float32)

        obs, _, terminated, truncated, _ = env.step(action_vals)
        episode_starts = terminated or truncated
        
        energy_kwh = (current_power_w * (900 / 3600)) / 1000.0 
        total_energy += energy_kwh
        
        if obs[9] < 23.0 or obs[9] > 26.0: 
            violations += 1
            
        if terminated or truncated: break
            
    env.close()
    return total_energy, violations

results = []
e1, v1 = run_ablation("1. PPO Only", use_lstm=False, use_shield=False)
results.append(["PPO-only", e1, v1])

e2, v2 = run_ablation("2. PPO + RBC", use_lstm=False, use_shield=True)
results.append(["PPO + Shield", e2, v2])

e3, v3 = run_ablation("3. LSTM + PPO", use_lstm=True, use_shield=False)
results.append(["LSTM + PPO", e3, v3])

e4, v4 = run_ablation("4. Full Hybrid", use_lstm=True, use_shield=True)
results.append(["Full Hybrid", e4, v4])

print("\n" + "="*70)
print(f"{'Configuration':<15} | {'Energy (kWh)':<12} | {'Violations'}")
print("-" * 70)
for r in results:
    print(f"{r[0]:<15} | {r[1]:<12.1f} | {r[2]}")
print("="*70)
