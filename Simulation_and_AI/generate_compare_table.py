import pandas as pd
import os

# ==========================================
# CONFIGURATION
# ==========================================
# You might need to adjust these paths if your folder structure is different for other cities
FILES = {
    "New York": {
        "DQN":    "models/DQN/results/dqn_results_final.csv",
        "PPO":    "models/PPO/results/ppo_final_results.csv",
        "PID":    "models/PID/results/pid_results.csv",
        "RBC":    "models/RBC/results/rbc_results.csv",
        "Hybrid": "models/Hybrid/results/hybrid_lstm_results.csv"
    },
          "Kuala Lumpur": {
         "DQN":    "models/DQN/results_kl/dqn_results_kl.csv",
         "PPO":    "models/PPO/results_kl/ppo_final_results_kl.csv",
         "PID":    "models/PID/results_kl/pid_results_kl.csv",
         "RBC":    "models/RBC/results_kl/rbc_results_kl.csv",
         "Hybrid": "models/Hybrid/results_kl/hybrid_results_kl.csv"
    },
    "Tokyo": {
         "DQN":    "models/DQN/results_tokyo/dqn_results_tokyo.csv",
         "PPO":    "models/PPO/results_tokyo/ppo_final_results_tokyo.csv",
         "PID":    "models/PID/results_tokyo/pid_results_tokyo.csv",
         "RBC":    "models/RBC/results_tokyo/rbc_results_tokyo.csv",
         "Hybrid": "models/Hybrid/results_tokyo/hybrid_results_tokyo.csv"
    }
}

def calculate_steady_accuracy(filepath):
    if not os.path.exists(filepath):
        return None # File missing
        
    df = pd.read_csv(filepath)
    temp_col = 'Temp' if 'Temp' in df.columns else 'real_temp'
    
    # === CRITICAL ACADEMIC STEP ===
    # Exclude first 24 hours (96 steps) to measure STEADY STATE performance
    if len(df) > 96:
        df_steady = df.iloc[96:] 
    else:
        df_steady = df # Fallback if file is too short

    safe_steps = df_steady[(df_steady[temp_col] >= 23.0) & (df_steady[temp_col] <= 26.0)].shape[0]
    return (safe_steps / len(df_steady)) * 100

def generate_regional_table():
    print("\n" + "="*80)
    print("🌍 TABLE 4.3: CROSS-REGIONAL ROBUSTNESS (Steady-State Accuracy)")
    print("="*80)
    
    # We want rows to be Algorithms, Columns to be Cities
    algorithms = ["DQN", "PPO", "PID", "RBC", "Hybrid"]
    
    data = []
    
    for algo in algorithms:
        row = {"Algorithm": algo}
        for city, paths in FILES.items():
            path = paths.get(algo, "missing")
            acc = calculate_steady_accuracy(path)
            
            if acc is not None:
                row[city] = f"{acc:.2f}%"
            else:
                row[city] = "-" # Data missing
        data.append(row)
        
    df_regional = pd.DataFrame(data)
    
    # Print neatly
    print(df_regional.to_markdown(index=False))
    
    # Save
    df_regional.to_csv("FINAL_TABLE_4_3_REGIONAL.csv", index=False)
    print("\n💾 Saved to FINAL_TABLE_4_3_REGIONAL.csv")

if __name__ == "__main__":
    generate_regional_table()
