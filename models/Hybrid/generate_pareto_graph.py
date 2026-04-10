import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# ==========================================
# 1. LOAD DATA
# ==========================================
# Make sure these match the files in your results folder!
df_base = pd.read_csv("results/baseline_evaluations.csv")
df_hybrid = pd.read_csv("results/hybrid_multi_seed_results.csv")

# Combine all data into one DataFrame
df = pd.concat([df_base, df_hybrid], ignore_index=True)

# ==========================================
# 2. STATISTICAL PROOF (T-TEST)
# ==========================================
print("="*60)
print("📊 FINAL THESIS STATISTICAL PROOF")
print("="*60)

rbc_energy = df[df['Algorithm'] == 'RBC']['Energy_kWh']
hybrid_energy = df[df['Algorithm'] == 'Hybrid']['Energy_kWh']

t_stat, p_value = stats.ttest_ind(rbc_energy, hybrid_energy)

print(f"Mean RBC Energy:    {rbc_energy.mean():.1f} kWh")
print(f"Mean Hybrid Energy: {hybrid_energy.mean():.1f} kWh")
print(f"T-Statistic:        {t_stat:.4f}")
print(f"P-Value:            {p_value:.5e}")

if p_value < 0.05:
    print("✅ CONCLUSION: Statistically Significant (p < 0.05)! You can publish this.")
else:
    print("❌ CONCLUSION: Not Statistically Significant.")

# ==========================================
# 3. GENERATE PARETO GRAPH
# ==========================================
plt.figure(figsize=(10, 6))
sns.set_theme(style="whitegrid")

# Plot the scatter points
sns.scatterplot(
    data=df, 
    x='Violations', 
    y='Energy_kWh', 
    hue='Algorithm', 
    style='Algorithm',
    s=150,           
    palette=['red', 'blue', 'green'], 
    markers=['X', 's', 'o']
)

# Formatting the Graph
plt.title("Pareto Frontier: Energy Efficiency vs. Thermal Comfort", fontsize=14, fontweight='bold')
plt.xlabel("Total Comfort Violations (Lower is Better)", fontsize=12, fontweight='bold')
plt.ylabel("Total Energy Consumption (kWh) (Lower is Better)", fontsize=12, fontweight='bold')

# Invert X axis so "Better" (zero violations) is on the right side of the graph
plt.gca().invert_xaxis()

plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(title="Controller Type", title_fontsize='11', fontsize='10', loc='upper left')

# Save the final image
output_file = "results/pareto_frontier.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print("="*60)
print(f"📈 GRAPH SAVED SUCCESSFULLY TO: {output_file}")
print("="*60)
