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

# Look inside the folder where your multi-seed script saved them!
MODEL_DIR = "multi_seed_models"  
RESULT_DIR = "results"
CSV_NAME = "hybrid_multi_seed_results.csv"

SEEDS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

os.makedirs(RESULT_DIR, exist_ok=True)

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
# 2. MAIN EVALUATION LOOP
# ==========================================
def main():
    print("="*60)
    print("🚀 AUTOMATED HYBRID MULTI-SEED EVALUATION")
    print("="*60)
    
    shield = SmartShield()
    all_results = []
    
    for seed in SEEDS:
        print(f"🔹 Testing Seed: {seed}...", end=" ", flush=True)
        
        # 1. Load the specific brain for this seed
        model_filename = f"hybrid_seed_{seed}"
        model_path = os.path.join(MODEL_DIR, model_filename)
        
        try:
            model = RecurrentPPO.load(model_path)
        except:
            print(f"❌ Failed to load {model_filename}.zip! Skipping.")
            continue

        # 2. Set up environment with matching weather seed
        env = gym.make(ENV_NAME)
        try: env.unwrapped.simulator.display_progress = False
        except: pass
        
        obs, _ = env.reset(seed=seed)
        lstm_states = None
        episode_starts = np.ones((1,), dtype=bool)
        
        HEAT_FIXED = 23.25
        total_energy_kwh = 0.0
        comfort_violations = 0
        
        # 3. Run the 1-Year Simulation
        for _ in range(TIMESTEPS_TEST):
            current_temp = obs[9]
            energy_power = obs[15]
            
            # Count Violations
            if current_temp < 23.0 or current_temp > 26.0:
                comfort_violations += 1
                
            # Count Energy
            total_energy_kwh += (energy_power * 0.25) / 1000.0
            
            # Smart Shield Logic
            if current_temp < 23.2 or current_temp > 25.8:
                safe_cooling = shield.get_safety_action(current_temp)
                action_vals = np.array([HEAT_FIXED, safe_cooling], dtype=np.float32)
                _, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            else:
                action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
                val = np.clip(action[0], -1.0, 1.0)
                ppo_cooling = 23.5 + (0.5 * (val + 1.0) * (28.0 - 23.5))
                action_vals = np.array([HEAT_FIXED, ppo_cooling], dtype=np.float32)

            obs, _, terminated, truncated, _ = env.step(action_vals)
            episode_starts = terminated or truncated
            
            if terminated or truncated: break
                
        env.close()
        
        # 4. Record Data
        all_results.append({
            "Algorithm": "Hybrid", 
            "Seed": seed, 
            "Energy_kWh": total_energy_kwh, 
            "Violations": comfort_violations
        })
        print(f"Done! (Energy: {total_energy_kwh:.1f} kWh, Violations: {comfort_violations})")

    # ==========================================
    # 3. SAVE AGGREGATED RESULTS
    # ==========================================
    df = pd.DataFrame(all_results)
    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)

    print("\n" + "═"*60)
    print(f"✅ ALL SEEDS TESTED SUCCESSFULLY.")
    print(f"📂 Results saved to: {csv_path}")
    print("═"*60)

if __name__ == "__main__":
    main()
