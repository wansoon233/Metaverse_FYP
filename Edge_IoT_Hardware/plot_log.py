import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ==========================================
# 1. LOAD AND CLEAN DATA
# ==========================================
df = pd.read_csv('Metaverse_FYP_Log.csv')
df.columns = df.columns.str.strip()

df['Indoor Temp (°C)'] = pd.to_numeric(df['Indoor Temp (°C)'], errors='coerce')
df['Outdoor Temp (°C)'] = pd.to_numeric(df['Outdoor Temp (°C)'], errors='coerce')
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

# Filter out boot-up values
df_clean = df[df['Actor'].isin(['LSTM_AI', 'Sensors'])].copy()
df_clean = df_clean[df_clean['Indoor Temp (°C)'] > 24.1]
df_clean = df_clean.dropna(subset=['Timestamp', 'Indoor Temp (°C)'])

# ==========================================
# 2. DRAW THE GRAPH
# ==========================================
fig, ax = plt.subplots(figsize=(12, 6))

# Plot the Indoor and Outdoor lines
ax.plot(df_clean['Timestamp'], df_clean['Indoor Temp (°C)'], label='Indoor Temp (AI Controlled)', color='#1f77b4', linewidth=2.5)
ax.plot(df_clean['Timestamp'], df_clean['Outdoor Temp (°C)'], label='Outdoor Temp (Ambient)', color='#ff7f0e', linestyle='--', linewidth=2)

# Highlight the Comfort Zone in Green
ax.axhspan(23.0, 26.0, color='green', alpha=0.15, label='Comfort Zone (23.0°C - 26.0°C)')

# Make it look professional
ax.set_title('Physical Hardware Validation: Sim-to-Real Control Authority', fontsize=16, fontweight='bold', pad=15)
ax.set_xlabel('Time', fontsize=12, fontweight='bold')
ax.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
ax.legend(loc='upper right', framealpha=0.9, shadow=True)
ax.grid(True, linestyle=':', alpha=0.7)

# Format the X-axis to show Time properly
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
plt.xticks(rotation=45)
plt.tight_layout()

# Save the image
plt.savefig('hardware_validation_plot.png', dpi=300)
print("✅ Success! Graph saved as 'hardware_validation_plot.png'")
