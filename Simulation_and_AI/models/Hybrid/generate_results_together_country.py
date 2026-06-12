import pandas as pd
import numpy as np
import os

# ==========================================
# 1. PATH CONFIGURATION
# ==========================================
results_map = {
    "Kuala Lumpur": "models/Hybrid/results_kl/hybrid_results_kl.csv",
    "Saudi Arabia": "models/Hybrid/results_saudi/hybrid_results_saudi.csv",
    "Tokyo": "models/Hybrid/results_tokyo/hybrid_results_tokyo.csv",
    "Iceland": "models/Hybrid/results_iceland/hybrid_results_iceland.csv"
}

def process_location(name, path):
    if not os.path.exists(path):
        return [name] + ["N/A"] * 5
    
    df = pd.read_csv(path)
    total_steps = len(df)
    
    # 1. Accuracy & Violations
    # Comfort range: 23.0°C to 26.0°C
    hits = len(df[(df['Temp'] >= 23.0) & (df['Temp'] <= 26.0)])
    accuracy = (hits / total_steps) * 100
    violations = total_steps - hits
    
    # 2. Energy Metrics (kWh)
    # 15 min steps = 0.25h. Energy = (Avg Power * Total Hours) / 1000
    total_kwh = (df['Power'].mean() * (total_steps * 0.25)) / 1000
    
    # 3. Brain Decisions & Results
    avg_setpoint = df['Setpoint'].mean() # The target chosen by the AI
    avg_temp = df['Temp'].mean()         # The actual resulting temp
    max_temp = df['Temp'].max()         # The worst-case spike

    return [
        name, 
        f"{accuracy:.2f}%",
        f"{violations}",
        f"{total_kwh:.2f}",
        f"{avg_setpoint:.2f}°C",
        f"{avg_temp:.2f}°C",
        f"{max_temp:.2f}°C"
    ]

# ==========================================
# 2. EXECUTION & FORMATTING
# ==========================================
table_data = []
for loc, path in results_map.items():
    table_data.append(process_location(loc, path))

headers = [
    "Location", "Accuracy", "Violations", "Total kWh", "Avg Setpoint", "Avg Temp", "Max Temp"
]

# Adjusting spacing for a clean look
print("\n" + "="*105)
print(f"{headers[0]:<22} | {headers[1]:<10} | {headers[2]:<10} | {headers[3]:<10} | {headers[4]:<12} | {headers[5]:<10} | {headers[6]:<10}")
print("-" * 105)

for r in table_data:
    print(f"{r[0]:<22} | {r[1]:<10} | {r[2]:<10} | {r[3]:<10} | {r[4]:<12} | {r[5]:<10} | {r[6]:<10}")

print("="*105 + "\n")
