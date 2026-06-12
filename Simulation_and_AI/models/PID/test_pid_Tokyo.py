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

RESULT_DIR = "models/PID/results_tokyo"
CSV_NAME = "pid_results_tokyo.csv"

os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. PID CONTROLLER
# ==========================================
class PIDController:
    def __init__(self, target=24.5):
        self.target = target
        self.Kp = 2.0
        self.Ki = 0.1
        self.Kd = 0.5
        self.prev_error = 0
        self.integral = 0
        
    def get_action(self, current_temp):
        error = current_temp - self.target
        self.integral += error
        self.integral = np.clip(self.integral, -5.0, 5.0) 
        
        P = self.Kp * error
        I = self.Ki * self.integral
        D = self.Kd * (error - self.prev_error)
        
        self.prev_error = error
        
        output = self.target - (P + I + D)
        return np.clip(output, 23.5, 28.0)

# ==========================================
# 2. MAIN
# ==========================================
def main():
    print("="*60)
    print("🚀 TESTING PID GENERALIZATION: TOKYO")
    print(f"   Weather: {NEW_WEATHER}")
    print("="*60)
    
    env = gym.make(ENV_NAME, weather_files=NEW_WEATHER)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    pid = PIDController(target=24.5)
    obs, _ = env.reset()
    hits, steps, logs = 0, 0, []
    HEAT_FIXED = 23.25
    
    for i in range(TIMESTEPS_TEST):
        current_temp = obs[9]
        cooling_setpoint = pid.get_action(current_temp)
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
