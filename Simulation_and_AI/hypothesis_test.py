import pandas as pd
import numpy as np
from scipy import stats
import os

# ==========================================
# CONFIGURATION
# ==========================================
# Compare Hybrid vs RBC (or PID)
FILE_A = "models/RBC/results/rbc_results.csv"      # Baseline
FILE_B = "models/Hybrid/results/hybrid_lstm_results.csv" # Hybrid Model

# Simulation Settings
STEPS_PER_HOUR = 4  # Assuming 15-minute intervals
HOURS_PER_DAY = 24
STEPS_PER_DAY = STEPS_PER_HOUR * HOURS_PER_DAY

def load_daily_energy(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found {file_path}")
        return None
        
    df = pd.read_csv(file_path)
    
    # Calculate Energy (kWh) per step: Power (Watts) * 0.25h / 1000
    df['Energy_kWh'] = (df['Power'] * 0.25) / 1000.0
    
    # Create a 'Day' column
    # Assume sequential steps: 1..96 = Day 1, 97..192 = Day 2, etc.
    df['Day'] = ((df['Step'] - 1) // STEPS_PER_DAY) + 1
    
    # Group by Day to get Total Daily Energy
    daily_data = df.groupby('Day')['Energy_kWh'].sum().reset_index()
    return daily_data['Energy_kWh']

def main():
    print("="*60)
    print("🧪 SCIENTIFIC HYPOTHESIS TESTING (Paired T-Test)")
    print("="*60)

    # 1. Load Data
    print(f"🔹 Loading Baseline: {FILE_A}")
    energy_baseline = load_daily_energy(FILE_A)
    
    print(f"🔹 Loading Proposed: {FILE_B}")
    energy_hybrid = load_daily_energy(FILE_B)

    if energy_baseline is None or energy_hybrid is None:
        return

    # Check if lengths match (must be paired!)
    if len(energy_baseline) != len(energy_hybrid):
        print("⚠️ Warning: Datasets have different lengths!")
        min_len = min(len(energy_baseline), len(energy_hybrid))
        energy_baseline = energy_baseline.iloc[:min_len]
        energy_hybrid = energy_hybrid.iloc[:min_len]

    # 2. Perform Paired T-Test
    # We use 'greater' if we expect Baseline > Hybrid (Energy Savings)
    # But usually, a standard 'two-sided' test is safer for thesis arguments
    t_stat, p_value = stats.ttest_rel(energy_baseline, energy_hybrid)

    # 3. Calculate Mean Differences
    mean_base = energy_baseline.mean()
    mean_hybrid = energy_hybrid.mean()
    savings = ((mean_base - mean_hybrid) / mean_base) * 100

    # 4. Results
    print("\n" + "-"*40)
    print("📊 STATISTICAL RESULTS")
    print("-"*40)
    print(f"Mean Daily Energy (Baseline): {mean_base:.2f} kWh")
    print(f"Mean Daily Energy (Hybrid):   {mean_hybrid:.2f} kWh")
    print(f"Average Savings:              {savings:.2f}%")
    print(f"T-Statistic:                  {t_stat:.4f}")
    print(f"P-Value:                      {p_value:.5e}") # Scientific notation

    # 5. Conclusion
    print("-"*40)
    alpha = 0.05
    if p_value < alpha:
        print("✅ CONCLUSION: REJECT NULL HYPOTHESIS")
        print("   The difference is STATISTICALLY SIGNIFICANT.")
        print("   You have proven scientifically that your model is different.")
    else:
        print("❌ CONCLUSION: FAIL TO REJECT NULL HYPOTHESIS")
        print("   The difference might be due to random chance.")
    print("="*60)

if __name__ == "__main__":
    main()
