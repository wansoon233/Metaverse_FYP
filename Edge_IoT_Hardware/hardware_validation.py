import pandas as pd

# ==========================================
# 1. LOAD AND CLEAN THE DATA
# ==========================================
try:
    try:
        df = pd.read_csv('Metaverse_FYP_Log.csv')
    except FileNotFoundError:
        df = pd.read_csv('Metaverse FYP Log.csv')
except FileNotFoundError:
    print("Error: Could not find your CSV file. Check the filename.")
    exit()

df.columns = df.columns.str.strip()

# Convert columns to numeric and datetime types
df['Indoor Temp (°C)'] = pd.to_numeric(df['Indoor Temp (°C)'], errors='coerce')
df['Outdoor Temp (°C)'] = pd.to_numeric(df['Outdoor Temp (°C)'], errors='coerce')
df['Latency (ms)'] = pd.to_numeric(df['Latency (ms)'], errors='coerce')
df['PMV'] = pd.to_numeric(df['PMV'], errors='coerce')
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

# Global cleanup: Remove the exact 24.0 Pi boot-up bug and drop empty rows
df_clean = df[df['Indoor Temp (°C)'] != 24.0].dropna(subset=['Timestamp', 'Indoor Temp (°C)'])

# ==========================================
# 2. Q1 DATABASE NORMALIZATION (ACTOR SEPARATION)
# ==========================================
# A. Environmental Ground Truth (Strictly Time-Series Normalized)
df_env = df_clean[df_clean['Actor'] == 'Sensors'].copy()

# Record the raw number of logs before filtering
raw_env_logs = len(df_env)

# THE PACKET LOSS FIX: Drop consecutive identical temperatures (Stale Data)
# This prevents network freezes from artificially inflating the accuracy and stability.
df_env = df_env.loc[df_env['Indoor Temp (°C)'].shift() != df_env['Indoor Temp (°C)']]

# Calculate how many frozen logs were dropped
total_env_logs = len(df_env)
stale_logs_dropped = raw_env_logs - total_env_logs

# B. AI Performance Logs (Asynchronous Event Triggers)
df_ai = df_clean[df_clean['Actor'] == 'LSTM_AI'].copy()

# C. Manual Override Logs (Specific Tablet HMI Latency)
# This strictly isolates Local Area Network (LAN) performance, ignoring future cloud/button inputs.
df_user = df_clean[(df_clean['Actor'] == 'USER') & (df_clean['Interface Mode'] == 'Tablet')].copy()

# ==========================================
# 3. SEPARATE STEADY-STATE VS STRESS TEST (Using Env Data)
# ==========================================
# Isolate the exact Hair Dryer test window based on manual log notes
stress_mask = (df_env['Timestamp'] >= '2026-05-02 22:32:00') & (df_env['Timestamp'] <= '2026-05-02 22:41:00')

df_steady_state = df_env[~stress_mask]

# ==========================================
# 4. CALCULATE METRICS (TROPICAL STANDARD: <= 26.5°C)
# ==========================================
LOWER_LIMIT = 23.0
UPPER_LIMIT = 26.5

total_steady_logs = len(df_steady_state)

# Calculate Accuracy (Time in Comfort) based ONLY on normalized Sensor Time
if total_env_logs > 0:
    hits_overall = len(df_env[(df_env['Indoor Temp (°C)'] >= LOWER_LIMIT) & (df_env['Indoor Temp (°C)'] <= UPPER_LIMIT)])
    accuracy_overall = (hits_overall / total_env_logs) * 100 
else:
    accuracy_overall = 0

if total_steady_logs > 0:
    hits_steady = len(df_steady_state[(df_steady_state['Indoor Temp (°C)'] >= LOWER_LIMIT) & (df_steady_state['Indoor Temp (°C)'] <= UPPER_LIMIT)])
    accuracy_steady = (hits_steady / total_steady_logs) * 100 
else:
    accuracy_steady = 0

# Thermal Metrics (From df_env strictly)
avg_in_temp = df_env['Indoor Temp (°C)'].mean()
max_in_temp = df_env['Indoor Temp (°C)'].max() 
std_in_temp = df_env['Indoor Temp (°C)'].std()
avg_pmv = df_env['PMV'].dropna().mean()

avg_out_temp = df_env['Outdoor Temp (°C)'].mean()
max_out_temp = df_env['Outdoor Temp (°C)'].max()

# Latency Metrics (From respective Actor DataFrames)
avg_ai_latency = df_ai['Latency (ms)'].dropna().mean()

avg_user_latency = df_user['Latency (ms)'].dropna().mean() if len(df_user) > 0 else 0

# ==========================================
# 5. PRINT OFFICIAL THESIS REPORT
# ==========================================
print("\n" + "="*85)
print(f"{'PHYSICAL HARDWARE VALIDATION REPORT (NORMALIZED TIME-SERIES)':^85}")
print("="*85)
print(f" Raw Sensor Telemetry         : {raw_env_logs}")
print(f" Stale/Timeout Packets Dropped: {stale_logs_dropped} (Edge Disconnects)")
print(f" Normalized Sensor Time-Steps : {total_env_logs} (1 Step = ~60 seconds)")
print(f" Total AI Event Triggers      : {len(df_ai)}")
print(f" Total Human Overrides        : {len(df_user)}")
print(f" Comfort Boundaries Assessed  : {LOWER_LIMIT:.1f} °C to {UPPER_LIMIT:.1f} °C")
print("-" * 85)
print(f" {'Metric':<34} | {'Value':<12} | {'Validation Context'}")
print("-" * 85)
print(f" {'Steady-State Time in Comfort':<34} | {accuracy_steady:>6.2f} %     | Normal Operations")
print(f" {'Robustness Time in Comfort':<34} | {accuracy_overall:>6.2f} %     | Includes Heat Stress")
print(f" {'Average PMV Score':<34} | {avg_pmv:>6.3f}        | Target: Neutral (0.0)")
print(f" {'Thermal Stability (Std)':<34} | {std_in_temp:>6.3f} °C     | Control Precision")
print("-" * 85)
print(f" {'Average Indoor Temp':<34} | {avg_in_temp:>6.2f} °C     | Target Acclimatization")
print(f" {'Peak Disturbance Temp (Inside)':<34} | {max_in_temp:>6.2f} °C     | Hair Dryer Maximum")
print(f" {'Peak Ambient Temp (Outside)':<34} | {max_out_temp:>6.2f} °C     | Room Maximum")
print("-" * 85)
print(f" {'Avg Autonomous Edge Latency':<34} | {avg_ai_latency:>6.2f} ms     | AI Inference CPU Speed")
if len(df_user) > 0:
    print(f" {'Avg Tablet HMI Override Latency':<34} | {avg_user_latency:>6.2f} ms     | Local LAN/Relay Speed")
print("="*85 + "\n")
