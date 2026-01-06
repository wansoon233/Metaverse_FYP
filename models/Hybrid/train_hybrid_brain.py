import gymnasium as gym
import numpy as np
import sinergym
import logging
import os  
from sb3_contrib import RecurrentPPO 
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

# ==========================================
# 0. CONFIG & PATHS
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'

TIMESTEPS_TRAIN = 80000 

# --- SAVE PATH CONFIGURATION ---
# This ensures the folder exists so you don't get an error
SAVE_DIR = "models/Hybrid/saved_models"
MODEL_NAME = "ppo_lstm_fast"
os.makedirs(SAVE_DIR, exist_ok=True) 

# ==========================================
# 1. PHYSICS WRAPPER
# ==========================================
class LSTMWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        
        self.HEAT_FIXED = 23.25      
        self.COOL_MIN = 23.5          
        self.COOL_MAX = 28.0          

    def step(self, action):
        val = np.clip(action[0], -1.0, 1.0)
        cooling_setpoint = self.COOL_MIN + (0.5 * (val + 1.0) * (self.COOL_MAX - self.COOL_MIN))
        
        dual_action = np.array([self.HEAT_FIXED, cooling_setpoint], dtype=np.float32)
        obs, _, terminated, truncated, info = self.env.step(dual_action)
        
        temp_c = obs[9]        
        energy_power = obs[15] 

        # Reward Function
        if 23.0 <= temp_c <= 26.0:
            dist = abs(temp_c - 24.5)
            score = 2.0 + (1.0 - dist)
        else:
            diff = min(abs(23.0 - temp_c), abs(temp_c - 26.0))
            score = -(diff * 5.0)

        energy_score = -1.0 * (energy_power / 10000.0)
        
        return obs, (score + energy_score), terminated, truncated, info

# ==========================================
# 2. LOGGER
# ==========================================
class CleanLogger(BaseCallback):
    def _on_step(self) -> bool:
        if self.n_calls % 5000 == 0:
            pct = (self.n_calls / TIMESTEPS_TRAIN) * 100
            print(f"   [Training] Step {self.n_calls}/{TIMESTEPS_TRAIN} ({pct:.0f}%)")
        return True

# ==========================================
# 3. MAIN TRAINING LOOP
# ==========================================
def main():
    print("="*60)
    print("🚀 TRAINING LSTM HYBRID BRAIN")
    print("="*60)
    
    env = gym.make(ENV_NAME)
    try: env.unwrapped.simulator.display_progress = False
    except: pass
    
    env = LSTMWrapper(env)
    env = Monitor(env)

    print(f"🔹 Initializing RecurrentPPO (LSTM)...")
    model = RecurrentPPO(
        "MlpLstmPolicy", 
        env, 
        verbose=0, 
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        ent_coef=0.01
    )

    print(f"🔹 Starting Training for {TIMESTEPS_TRAIN} steps...")
    callback = CleanLogger()
    model.learn(total_timesteps=TIMESTEPS_TRAIN, callback=callback)
    
    # --- UPDATED SAVE COMMAND ---
    # Combines the folder path and file name
    save_path = os.path.join(SAVE_DIR, MODEL_NAME)
    model.save(save_path)
    
    print("="*60)
    print("✅ TRAINING COMPLETE.")
    print(f"   Saved to: {save_path}.zip")
    print("   NOW you can run the testing script.")
    print("="*60)
    env.close()

if __name__ == "__main__":
    main()
