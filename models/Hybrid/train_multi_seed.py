import gymnasium as gym
import numpy as np
import sinergym
import logging
import os  
from sb3_contrib import RecurrentPPO 

# ==========================================
# 0. CONFIG & PATHS
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
ENV_NAME = 'Eplus-5zone-mixed-continuous-v1'
TIMESTEPS_TRAIN = 80000 
SAVE_DIR = "multi_seed_models"
os.makedirs(SAVE_DIR, exist_ok=True) 

# The 10 distinct random seeds we will test
SEEDS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

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

        if 23.0 <= temp_c <= 26.0:
            score = 2.0 + (1.0 - abs(temp_c - 24.5))
        else:
            score = -(min(abs(23.0 - temp_c), abs(temp_c - 26.0)) * 5.0)

        return obs, (score - (energy_power / 10000.0)), terminated, truncated, info

# ==========================================
# 2. MAIN AUTOMATED LOOP
# ==========================================
def main():
    print("="*60)
    print("🚀 STARTING AUTOMATED MULTI-SEED TRAINING (N=10)")
    print("="*60)
    
    for current_seed in SEEDS:
        print(f"\n🔹 --- TRAINING SEED {current_seed} --- 🔹")
        
        env = gym.make(ENV_NAME)
        try: env.unwrapped.simulator.display_progress = False
        except: pass
        env = LSTMWrapper(env)

        # Initialize the Brain with the SPECIFIC SEED
        model = RecurrentPPO(
            "MlpLstmPolicy", 
            env, 
            verbose=0, 
            seed=current_seed, # <--- THIS IS THE MAGIC VARIABLE
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64
        )

        # Train the model
        model.learn(total_timesteps=TIMESTEPS_TRAIN)
        
        # Save this specific seed's brain
        save_path = os.path.join(SAVE_DIR, f"hybrid_seed_{current_seed}")
        model.save(save_path)
        print(f"✅ Saved Brain to: {save_path}.zip")
        
        env.close()

    print("\n" + "="*60)
    print("🎉 ALL 10 SEEDS TRAINED SUCCESSFULLY!")
    print("="*60)

if __name__ == "__main__":
    main()
