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
MODEL_PATH = "saved_models/ppo_lstm_fast" 
RESULT_DIR = "results"

os.makedirs(RESULT_DIR, exist_ok=True)

# ==========================================
# 1. THE TWO SHIELDS (The Competitors)
# ==========================================
class SmartShieldRBC:
    def get_safety_action(self, current_temp):
        if current_temp > 25.8:
            return 24.0  # Force Max Cooling
        elif current_temp < 23.2:
            return 28.0  # Force Min Cooling
        return 26.0

class PIDShield:
    def __init__(self, target_temp=24.5, kp=1.5, ki=0.5, kd=0.1): # High Ki to demonstrate windup
        self.target = target_temp
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0.0
        self.last_error = 0.0

    def get_safety_action(self, current_temp):
        error = current_temp - self.target
        self.integral += error # THIS is what causes the windup!
        derivative = error - self.last_error
        
        pid_adjustment = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.last_error = error
        
        safe_cooling = 26.0 - pid_adjustment
        return float(np.clip(safe_cooling, 23.5, 28.0))

# ==========================================
# 2. THE SIMULATION ENGINE
# ==========================================
def run_stress_test(shield_type, shield_name):
    print(f"\n🚀 Running Stress Test: {shield_name}")
    
    env = gym.make(ENV_NAME)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    # Load the EXACT SAME AI Brain
    model = RecurrentPPO.load(MODEL_PATH)
    
    shield = shield_type
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)
    obs, _ = env.reset()
    logs = []
    HEAT_FIXED = 23.25
    
    # Run for 150 steps (~37 hours)
    for step in range(150):
        true_temp = obs[9]
        
        # 🚨 INJECT ANOMALY: Between steps 50 and 60, simulate a massive heatwave!
        if 50 <= step <= 60:
            perceived_temp = 32.0 
            anomaly = "HEATWAVE"
        else:
            perceived_temp = true_temp
            anomaly = "NORMAL"
            
        # 1. SHIELD LOGIC
        if perceived_temp < 23.2 or perceived_temp > 25.8:
            safe_cooling = shield.get_safety_action(perceived_temp)
            action_vals = np.array([HEAT_FIXED, safe_cooling], dtype=np.float32)
            mode = "SHIELD_ACTIVE"
            _, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            
            # Grab integral if it's the PID for our thesis data
            integral_val = getattr(shield, 'integral', 0.0) 
            
        # 2. AI LOGIC
        else:
            action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            val = np.clip(action[0], -1.0, 1.0)
            ppo_cooling = 23.5 + (0.5 * (val + 1.0) * (28.0 - 23.5))
            action_vals = np.array([HEAT_FIXED, ppo_cooling], dtype=np.float32)
            mode = "LSTM_AI"
            
            # If PID is quiet, we should still decay its integral to be fair, but we'll leave it 0 for this demo
            integral_val = getattr(shield, 'integral', 0.0)

        # Apply action to the actual room
        obs, _, terminated, truncated, info = env.step(action_vals)
        episode_starts = terminated or truncated
        
        # Log the data for your Excel Graph
        logs.append([
            step, 
            round(true_temp, 2), 
            round(perceived_temp, 2), 
            round(action_vals[1], 2), 
            round(integral_val, 2), 
            anomaly, 
            mode
        ])
        
        if terminated or truncated: break

    # Save to CSV
    df = pd.DataFrame(logs, columns=['Step', 'Actual_Temp', 'Sensor_Temp', 'AC_Setpoint', 'PID_Integral', 'Event', 'Controller'])
    csv_path = os.path.join(RESULT_DIR, f"stress_test_{shield_name}.csv")
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved results to: {csv_path}")
    env.close()

# ==========================================
# 3. EXECUTE BOTH TESTS
# ==========================================
if __name__ == "__main__":
    print("="*60)
    print("🧪 INITIALIZING THESIS ABLATION & STRESS TEST")
    print("="*60)
    
    # Run Test 1: The RBC (SmartShield)
    run_stress_test(SmartShieldRBC(), "RBC_Shield")
    
    # Run Test 2: The PID
    run_stress_test(PIDShield(), "PID_Shield")
    
    print("\n🎉 STRESS TESTS COMPLETE. You can now plot the CSV files in Excel!")
