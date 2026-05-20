import gymnasium as gym
import numpy as np
import sinergym
import logging
import os  
import torch 
import mlflow
import mlflow.pytorch
from sb3_contrib import RecurrentPPO 
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

# ==========================================
# 0. CONFIG 
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
KL_WEATHER_PATH = '/home/wansoon/Desktop/FYP_Metaverse/sinergym_source/sinergym/data/weather/KualaLumpur.epw' 

TIMESTEPS_TRAIN = 300000 
SAVE_DIR = "models/Hybrid/saved_models"
MODEL_NAME = "ppo_lstm"
os.makedirs(SAVE_DIR, exist_ok=True) 

mlflow.set_experiment("Hybrid-LSTM-PPO")

# ==========================================
# 1. THE 2D WRAPPER (KL & Sinergym Safe)
# ==========================================
class EliteWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
        
        # Hard limits enforced by Sinergym physics
        self.HEAT_MIN, self.HEAT_MAX = 12.0, 23.25 
        self.COOL_MIN, self.COOL_MAX = 23.5, 30.0          

    def step(self, action):
        val_heat = np.clip(action[0], -1.0, 1.0)
        val_cool = np.clip(action[1], -1.0, 1.0)
        
        h_set = self.HEAT_MIN + (0.5 * (val_heat + 1.0) * (self.HEAT_MAX - self.HEAT_MIN))
        c_set = self.COOL_MIN + (0.5 * (val_cool + 1.0) * (self.COOL_MAX - self.COOL_MIN))
        
        dual_action = np.array([h_set, c_set], dtype=np.float32)
        obs, _, terminated, truncated, info = self.env.step(dual_action)
        
        temp = obs[9]        
        power = obs[15] 

        # Smooth, precision-focused reward curve
        comfort_reward = 10.0 * np.exp(-0.5 * ((temp - 24.5) / 1.0) ** 2) 
        energy_penalty = (power / 10000.0) * 0.5 

        reward = comfort_reward - energy_penalty
        
        return obs, reward, terminated, truncated, info

# ==========================================
# 2. CALLBACKS & MAIN
# ==========================================
class ProgressLogger(BaseCallback):
    def _on_step(self) -> bool:
        if self.n_calls % 10000 == 0:
            print(f"🚀 Step {self.n_calls}/{TIMESTEPS_TRAIN}...")
        return True

def main():
    print("="*60)
    print("🚀 TRAINING KL-SPECIALIST BRAIN")
    print("="*60)
    
    with mlflow.start_run(run_name="Hybrid_KL_Training"):
        env = Monitor(EliteWrapper(gym.make(ENV_NAME, weather_files=KL_WEATHER_PATH)))

        model = RecurrentPPO(
            "MlpLstmPolicy", 
            env, 
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64, 
            ent_coef=0.01, 
            verbose=0
        )

        model.learn(total_timesteps=TIMESTEPS_TRAIN, callback=ProgressLogger())
        
        model.save(os.path.join(SAVE_DIR, MODEL_NAME))
        torch.save(model.policy.state_dict(), os.path.join(SAVE_DIR, 'lstm_weights.pth'))
        
        print("✅ KL TRAINING COMPLETE.")
        env.close()

if __name__ == "__main__":
    main()
