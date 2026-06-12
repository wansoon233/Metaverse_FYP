import gymnasium as gym
import numpy as np
import sinergym
import pandas as pd
import logging
import os

# ==========================================
# 0. CONFIG 
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
KL_WEATHER_PATH = '/home/wansoon/Desktop/FYP_Metaverse/sinergym_source/sinergym/data/weather/KualaLumpur.epw' 
RESULT_DIR = "/home/wansoon/Desktop/FYP_Metaverse/models/Hybrid/results"
os.makedirs(RESULT_DIR, exist_ok=True)

SEEDS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
STEPS_PER_EPISODE = 35040 # 1 Full Year

# ==========================================
# 1. THE CONTROLLERS
# ==========================================
class SmartShieldRBC:
    def get_action(self, current_temp):
        if current_temp > 25.8: return 24.0
        elif current_temp < 23.2: return 28.0
        return 26.0

class PIDShield:
    def __init__(self, target=24.5, kp=1.5, ki=0.01, kd=0.1):
        self.target = target
        self.kp, self.ki, self.kd = kp, ki, kd
        self.integral, self.last_error = 0.0, 0.0

    def get_action(self, current_temp):
        error = current_temp - self.target
        self.integral += error
        derivative = error - self.last_error
        self.last_error = error
        
        pid_output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        cooling_sp = 26.0 - pid_output 
        return np.clip(cooling_sp, 23.5, 30.0)

# ==========================================
# 2. EVALUATION FUNCTION
# ==========================================
def evaluate_controller(controller_name, controller_class):
    print(f"\n🚀 Evaluating Baseline: {controller_name}")
    results = []
    
    for seed in SEEDS:
        print(f"   🌱 Seed {seed}...", end=" ")
        env = gym.make(ENV_NAME, weather_files=KL_WEATHER_PATH)
        try: env.unwrapped.simulator.display_progress = False
        except: pass
        
        obs, _ = env.reset(seed=seed)
        controller = controller_class()
        
        total_energy = 0.0
        comfort_violations = 0
        
        for _ in range(STEPS_PER_EPISODE):
            temp_c = obs[9]
            energy_power = obs[15]
            
            if temp_c < 23.0 or temp_c > 26.0:
                comfort_violations += 1
                
            total_energy += (energy_power * 0.25) / 1000.0 
            
            cooling_sp = controller.get_action(temp_c)
            # HARDCODED Sinergym Limit for Baselines
            action = np.array([23.25, cooling_sp], dtype=np.float32) 
            
            obs, _, terminated, truncated, _ = env.step(action)
            if terminated or truncated:
                break
                
        results.append({"Algorithm": controller_name, "Seed": seed, "Energy_kWh": total_energy, "Violations": comfort_violations})
        print(f"Done! (Energy: {total_energy:.1f} kWh, Violations: {comfort_violations})")
        env.close()
        
    return results

# ==========================================
# 3. EXECUTE
# ==========================================
if __name__ == "__main__":
    all_results = []
    all_results.extend(evaluate_controller("RBC", SmartShieldRBC))
    all_results.extend(evaluate_controller("PID", PIDShield))
    
    df = pd.DataFrame(all_results)
    csv_path = os.path.join(RESULT_DIR, "baseline_evaluations.csv")
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Baselines saved to {csv_path}")
