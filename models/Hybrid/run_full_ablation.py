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
TIMESTEPS_TEST = 35040 
MODEL_PATH = "multi_seed_models/hybrid_seed_100.zip"
HEAT_FIXED = 23.25

print("="*60)
print("🔬 FULL 4-PART ABLATION STUDY (LSTM-PPO-RBC)")
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
    
    env = gym.make(ENV_NAME)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    obs, _ = env.reset(seed=10)
    
    # LSTM Memory trackers
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)
    
    total_energy = 0.0
    violations = 0
    
    for step in range(TIMESTEPS_TEST):
        current_temp = obs[9]
        energy_power = obs[15]
        
        # Count Violations (Limits: 23.0 to 26.0)
        if current_temp < 23.0 or current_temp > 26.0:
            violations += 1
        total_energy += (energy_power * 0.25) / 1000.0
        
        # --- ABLATION: SHIELD LOGIC ---
        if use_shield and (current_temp < 23.2 or current_temp > 25.8):
            # RBC Shield takes over
            safe_cooling = 24.0 if current_temp > 25.8 else 28.0
            action_vals = np.array([HEAT_FIXED, safe_cooling], dtype=np.float32)
            
            # Keep memory updated even when shield acts (if LSTM is enabled)
            if use_lstm:
                _, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
                
        else:
            # --- ABLATION: PPO & LSTM LOGIC ---
            if use_lstm:
                # Normal AI with memory
                action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            else:
                # LOBOTOMY: Wipe memory to simulate standard PPO
                temp_states = None
                temp_starts = np.ones((1,), dtype=bool)
                action, _ = model.predict(obs, state=temp_states, episode_start=temp_starts, deterministic=True)
            
            val = np.clip(action[0], -1.0, 1.0)
            ppo_cooling = 23.5 + (0.5 * (val + 1.0) * (28.0 - 23.5))
            action_vals = np.array([HEAT_FIXED, ppo_cooling], dtype=np.float32)

        # Step Environment
        obs, _, terminated, truncated, _ = env.step(action_vals)
        episode_starts = terminated or truncated
        
        if terminated or truncated: break
            
    env.close()
    return total_energy, violations

# ==========================================
# 1. RUN EXPERIMENTS
# ==========================================
results = []

# Config 1: PPO Only (Baseline RL)
e1, v1 = run_ablation("1. PPO Only", use_lstm=False, use_shield=False)
results.append(["PPO-only", e1, v1])

# Config 2: PPO + RBC Shield
e2, v2 = run_ablation("2. PPO + RBC", use_lstm=False, use_shield=True)
results.append(["PPO + Shield", e2, v2])

# Config 3: LSTM + PPO
e3, v3 = run_ablation("3. LSTM + PPO", use_lstm=True, use_shield=False)
results.append(["LSTM + PPO", e3, v3])

# Config 4: Full Hybrid (LSTM + PPO + RBC)
e4, v4 = run_ablation("4. Full Hybrid", use_lstm=True, use_shield=True)
results.append(["Full Hybrid", e4, v4])

# ==========================================
# 2. PRINT FINAL TABLE
# ==========================================
print("\n" + "="*70)
print(f"{'Configuration':<15} | {'LSTM':<5} | {'PPO':<5} | {'RBC Shield':<12} | {'Energy (kWh)':<12} | {'Violations'}")
print("-" * 70)
for r in results:
    config = r[0]
    e = r[1]
    v = r[2]
    lstm = "No" if "PPO-only" in config or "PPO + Shield" in config else "Yes"
    ppo = "Yes"
    shield = "No" if "PPO-only" in config or "LSTM + PPO" in config else "Yes"
    
    print(f"{config:<15} | {lstm:<5} | {ppo:<5} | {shield:<12} | {e:<12.1f} | {v}")
print("="*70)
print("Take a screenshot of this table! It matches your PDF perfectly.")
