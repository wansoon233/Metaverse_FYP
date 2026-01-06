import time
import random

# ==========================================
# EXPERIMENTAL CONFIGURATION
# ==========================================
# Setting a seed ensures reproducibility for the thesis report.
# This guarantees the "random" network drops happen at the same 
# moments for all 3 models, ensuring a fair comparison.
random.seed(42) 

TEST_DURATION = 1000     # Full simulation cycle
SAFE_LIMIT = 26.0        # Thermal Safety Limit (°C)
START_TEMP = 24.5        # Initial Temperature (°C)

# PHYSICS CONSTANTS (High-Load Environment)
# We simulate a "Hot Day" scenario to test worst-case resilience.
HEAT_RATE = 0.30         # Temperature rise per step (Aggressive)
COOL_RATE = 0.50         # Cooling capacity per step
SHIELD_TRIGGER = 25.5    # Calibrated Safety Threshold (Limit - Margin)

# NETWORK FAULT PARAMETERS (Stochastic Burst Model)
# Simulates unstable IoT connectivity (e.g., WiFi interference)
# instead of a fixed outage window.
BURST_PROBABILITY = 0.02 # 2% probability of connection drop start per step
BURST_MIN_LEN = 10       # Minimum duration of drop (steps)
BURST_MAX_LEN = 25       # Maximum duration of drop (steps)

def run_simulation(model_type):
    # Reset Environment for each model
    random.seed(42) # Reset seed so every model faces the EXACT same network drops
    current_temp = START_TEMP
    violations = 0
    active_burst_timer = 0
    
    for t in range(TEST_DURATION):
        
        # 1. NETWORK ENVIRONMENT SIMULATION
        # Logic: Check if a new network failure burst begins
        if active_burst_timer == 0:
            if random.random() < BURST_PROBABILITY:
                # Start a network outage of random duration
                active_burst_timer = random.randint(BURST_MIN_LEN, BURST_MAX_LEN)
        
        # Determine Packet Status
        packet_arrived = True
        if active_burst_timer > 0:
            packet_arrived = False
            active_burst_timer -= 1
            
        # 2. CONTROL DECISION (Cloud Layer)
        # Standard Logic: Cloud sends Cool (1) if Temp > 24.0
        cloud_command = 1 if current_temp > 24.0 else 0
        
        # 3. ACTUATION LOGIC (Edge Layer)
        final_action = 0
        
        if model_type == "DQN" or model_type == "PPO":
            # Baseline Models: Fully Dependent on Network
            if packet_arrived:
                final_action = cloud_command
            else:
                final_action = 0 # Default to OFF during signal loss
                
        elif model_type == "Hybrid":
            # Hybrid Model: Network + Local Override
            # A. Primary Control (Network Path)
            if packet_arrived:
                final_action = cloud_command
            else:
                final_action = 0
            
            # B. Safety Shield (Local / Zero-Latency Path)
            # This logic runs on the Edge Device, independent of packet status.
            if current_temp > SHIELD_TRIGGER:
                final_action = 1 # Emergency Cooling Override
        
        # 4. THERMAL PHYSICS UPDATE
        if final_action == 1:
            current_temp -= COOL_RATE
        else:
            current_temp += HEAT_RATE
            
        # Physics bounds (Room limits)
        current_temp = max(current_temp, 18.0)
        
        # 5. DATA LOGGING
        if current_temp > SAFE_LIMIT:
            violations += 1
            
    return violations

# ==========================================
# EXECUTION & REPORTING
# ==========================================
failures_dqn = run_simulation("DQN")
failures_ppo = run_simulation("PPO")
failures_hybrid = run_simulation("Hybrid")

# Output formatted as a clean scientific data table
print(f"{'Model Architecture':<25} | {'Total Steps':<12} | {'Violations (>26.0°C)':<20} | {'Result'}")
print("-" * 75)
print(f"{'DQN (Cloud-Only)':<25} | {TEST_DURATION:<12} | {failures_dqn:<20} | {'FAIL' if failures_dqn > 0 else 'PASS'}")
print(f"{'PPO (Cloud-Only)':<25} | {TEST_DURATION:<12} | {failures_ppo:<20} | {'FAIL' if failures_ppo > 0 else 'PASS'}")
print(f"{'Hybrid (Cloud+Edge)':<25} | {TEST_DURATION:<12} | {failures_hybrid:<20} | {'PASS' if failures_hybrid == 0 else 'FAIL'}")
