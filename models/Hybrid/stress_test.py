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
KL_WEATHER_PATH = '/home/wansoon/Desktop/FYP_Metaverse/sinergym_source/sinergym/data/weather/KualaLumpur.epw' 

MODEL_PATH = "/home/wansoon/Desktop/FYP_Metaverse/models/Hybrid/saved_models/ppo_lstm.zip" 
RESULT_DIR = "/home/wansoon/Desktop/FYP_Metaverse/models/Hybrid/results"
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
    def __init__(self, target_temp=24.5, kp=1.5, ki=0.5, kd=0.1): 
        # High Ki explicitly used to demonstrate Integral Windup failure!
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
        self.last_error = error
        
        pid_output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        # Convert PID output to an AC Setpoint
        cooling_sp = 26.0 - pid_output 
        return np.clip(cooling_sp, 23.5, 30.0)

# ==========================================
# 2. THE STRESS TEST LOOP
# ==========================================
def run_stress_test(shield_name, shield_class):
    print(f"\n⏳ Running Stress Test for: {shield_name}")
    
    env = gym.make(ENV_NAME, weather_files=KL_WEATHER_PATH)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    obs, _ = env.reset(seed=42)
    
    try:
        model = RecurrentPPO.load(MODEL_PATH)
    except:
        print(f"❌ Failed to load {MODEL_PATH}")
        return

    shield = shield_class()
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)
    logs = []
    
    # 3000 steps is about 1 month. Perfect for a zoomed-in Excel graph.
    TEST_STEPS = 3000 
    
    for step in range(TEST_STEPS):
        true_temp = obs[9]
        
        # --- THE ANOMALY INJECTION ---
        # Introduce a sudden +4.0°C fake sensor reading between step 1000 and 1500
        anomaly = 0.0
        if 1000 <= step <= 1500:
            anomaly = 4.0 
            
        perceived_temp = true_temp + anomaly
        integral_val = getattr(shield, 'integral', 0.0)
        
        # --- HYBRID LOGIC ---
        # The shield triggers based on what the SENSOR reads (perceived_temp)
        if perceived_temp < 23.2 or perceived_temp > 25.8:
            safe_cooling = shield.get_safety_action(perceived_temp)
            action_vals = np.array([23.25, safe_cooling], dtype=np.float32)
            mode = "SHIELD"
            
            # Keep AI memory synced
            _, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            integral_val = getattr(shield, 'integral', 0.0)
        else:
            action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
            
            val_heat = np.clip(action[0], -1.0, 1.0)
            val_cool = np.clip(action[1], -1.0, 1.0)
            
            # 2D Sinergym-Safe Decoding
            heating_setpoint = 12.0 + (0.5 * (val_heat + 1.0) * (23.25 - 12.0))
            cooling_setpoint = 23.5 + (0.5 * (val_cool + 1.0) * (30.0 - 23.5))
            
            action_vals = np.array([heating_setpoint, cooling_setpoint], dtype=np.float32)
            mode = "AI"

        # Apply action to the actual room
        obs, _, terminated, truncated, info = env.step(action_vals)
        episode_starts = terminated or truncated
        
        # Log data for Excel
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
    print("🧪 INITIALIZING THESIS SENSOR FAULT STRESS TEST")
    print("="*60)
    
    # Run Test 1: The RBC (SmartShield)
    run_stress_test("RBC", SmartShieldRBC)
    
    # Run Test 2: The PID (The Flawed Baseline)
    run_stress_test("PID", PIDShield)
    
    print("="*60)
    print("🎉 STRESS TESTS COMPLETE. OPEN CSVs IN EXCEL TO PLOT!")
