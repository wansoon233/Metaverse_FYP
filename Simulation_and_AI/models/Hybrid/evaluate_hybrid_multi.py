import sys
import logging
import gymnasium as gym
import sinergym
import torch
import numpy as np
import pandas as pd
import mlflow
from sb3_contrib import RecurrentPPO
import os

print("🚀 Starting Multi-Seed Evaluation (N=10, seeds 10-100)...", flush=True)

# ==========================================
# 0. CONFIG & PATHS
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
KL_WEATHER_PATH = '/home/wansoon/Desktop/FYP_Metaverse/sinergym_source/sinergym/data/weather/KualaLumpur.epw'

MULTI_SEED_MODEL_DIR = "/home/wansoon/Desktop/FYP_Metaverse/models/Hybrid/multi_seed_models"
RESULT_DIR = "/home/wansoon/Desktop/FYP_Metaverse/models/Hybrid/results"
CSV_NAME = "hybrid_multi_seed_results.csv"

os.makedirs(RESULT_DIR, exist_ok=True)
mlflow.set_experiment("Hybrid-LSTM-PPO")

TIMESTEPS_EVAL = 35040

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
# 2. MULTI-SEED EVALUATION LOOP
# ==========================================
def main():
    shield = SmartShield()
    all_results = []

    for seed_num in range(10, 101, 10):  # Seeds: 10, 20, 30, ..., 100
        print(f"\n🌱 Evaluating Seed {seed_num}", flush=True)

        # Load per-seed trained model
        model_filename = f"hybrid_seed_{seed_num}"
        model_path = os.path.join(MULTI_SEED_MODEL_DIR, model_filename)
        try:
            model = RecurrentPPO.load(model_path)
            print(f"  ✅ Loaded: {model_path}.zip")
        except Exception as e:
            print(f"  ❌ Model not found: {model_path}.zip — skipping ({e})")
            continue

        # Fresh environment for each seed
        env = gym.make(ENV_NAME, weather_files=KL_WEATHER_PATH)
        try:
            env.unwrapped.simulator.display_progress = False
        except:
            pass

        with mlflow.start_run(run_name=f"Hybrid_Eval_Seed_{seed_num}"):
            obs, info = env.reset(seed=seed_num)
            lstm_states = None
            episode_starts = np.ones((1,), dtype=bool)

            total_energy_kwh = 0.0
            comfort_violations = 0
            hits = 0
            total_gaussian_comfort = 0.0
            shield_activations = []

            for step in range(TIMESTEPS_EVAL):
                current_temp = obs[9]
                current_power_w = obs[15]

                # --- HYBRID LOGIC ---
                if current_temp < 23.2 or current_temp > 25.8:
                    safe_cooling = shield.get_safety_action(current_temp)
                    action_vals = np.array([23.25, safe_cooling], dtype=np.float32)
                    shield_activations.append(1)
                    _, lstm_states = model.predict(
                        obs, state=lstm_states, episode_start=episode_starts, deterministic=True
                    )
                else:
                    action, lstm_states = model.predict(
                        obs, state=lstm_states, episode_start=episode_starts, deterministic=True
                    )
                    val_heat = np.clip(action[0], -1.0, 1.0)
                    val_cool = np.clip(action[1], -1.0, 1.0)

                    # MATCHING THE TRAINING SCRIPT BOUNDS (12.0 to 23.25)
                    heating_setpoint = 12.0 + (0.5 * (val_heat + 1.0) * (23.25 - 12.0))
                    cooling_setpoint = 23.5 + (0.5 * (val_cool + 1.0) * (30.0 - 23.5))

                    action_vals = np.array([heating_setpoint, cooling_setpoint], dtype=np.float32)
                    shield_activations.append(0)

                # --- ENVIRONMENT STEP ---
                obs, reward, terminated, truncated, info = env.step(action_vals)
                episode_starts = terminated or truncated

                # --- METRICS ---
                new_temp = obs[9]
                new_power = obs[15]

                energy_kwh = (new_power * (900 / 3600)) / 1000.0
                total_energy_kwh += energy_kwh

                comfort_score = np.exp(-0.5 * ((new_temp - 24.5) / 1.0) ** 2)
                total_gaussian_comfort += comfort_score

                if 23.0 <= new_temp <= 26.0:
                    hits += 1
                else:
                    comfort_violations += 1

                if step % 10000 == 0 and step > 0:
                    print(f"   ...Step {step}/{TIMESTEPS_EVAL} | Temp: {new_temp:.2f}°C", flush=True)

                if terminated or truncated:
                    break

            # --- LOGGING TO MLFLOW ---
            avg_comfort_score = total_gaussian_comfort / TIMESTEPS_EVAL
            shield_rate = (sum(shield_activations) / TIMESTEPS_EVAL) * 100
            final_acc = (hits / TIMESTEPS_EVAL) * 100

            # PMV approximation (simplified, for logging only)
            pmv_approx = abs(new_temp - 24.5) / 10.0

            mlflow.log_metrics({
                "Total_Energy_kWh": total_energy_kwh,
                "Comfort_Violations": comfort_violations,
                "Avg_Comfort_Score": avg_comfort_score,
                "Shield_Activation_Pct": shield_rate,
                "Accuracy_Pct": final_acc,
                "PMV_Approx": pmv_approx
            })

            print(f"  📊 Seed {seed_num}: Energy={total_energy_kwh:.1f} kWh | "
                  f"Violations={comfort_violations} | Avg Comfort={avg_comfort_score:.3f} | "
                  f"Acc={final_acc:.2f}%", flush=True)

            all_results.append({
                "Algorithm": "Hybrid",
                "Seed": seed_num,
                "Energy_kWh": total_energy_kwh,
                "Violations": comfort_violations,
                "Avg_Comfort": avg_comfort_score,
                "Accuracy": final_acc,
                "PMV_Approx": pmv_approx
            })

        env.close()

    # ==========================================
    # 3. FINAL STATISTICAL OUTPUT
    # ==========================================
    df = pd.DataFrame(all_results)
    print("\n" + "=" * 60)
    print(f"🏆 FINAL RESULTS (Averaged across {len(df)} seeds)")
    print("=" * 60)
    print(f"Average Energy:     {df['Energy_kWh'].mean():.1f} kWh (±{df['Energy_kWh'].std():.1f})")
    print(f"Average Accuracy:   {df['Accuracy'].mean():.2f}% (±{df['Accuracy'].std():.2f})")
    print(f"Average Violations: {df['Violations'].mean():.1f} (±{df['Violations'].std():.1f})")
    print(f"Average Comfort:    {df['Avg_Comfort'].mean():.3f} (±{df['Avg_Comfort'].std():.3f})")
    print("=" * 60)

    csv_path = os.path.join(RESULT_DIR, CSV_NAME)
    df.to_csv(csv_path, index=False)
    print(f"✅ Results saved to: {csv_path}")

if __name__ == "__main__":
    main()
