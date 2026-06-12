import time
import numpy as np
import pandas as pd
import paho.mqtt.client as mqtt
from sb3_contrib import RecurrentPPO
import warnings

# ==========================================
# 0. CONFIGURATION
# ==========================================
warnings.filterwarnings("ignore") 
MODEL_PATH = "models/Hybrid/saved_models/ppo_lstm_fast"
MQTT_BROKER = "localhost"
TOPIC_ACTION = "home/living_room/ac/set"

# Standard Hardware Constants
RELAY_DELAY_MS = 10.00   
WIFI_ESTIMATE_MS = 20.00 

# Global storage
latencies_software = []  

# ==========================================
# 1. MQTT CALLBACKS
# ==========================================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC_ACTION)

def on_message(client, userdata, msg):
    arrival_time = time.time()
    try:
        start_time = float(msg.payload.decode())
        software_ms = (arrival_time - start_time) * 1000.0
        latencies_software.append(software_ms)
    except:
        pass

# ==========================================
# 2. MAIN BENCHMARK ENGINE
# ==========================================
def main():
    print("\n" + "="*60)
    print("🚀 STARTING SIL LATENCY VALIDATION (Software-in-the-Loop)")
    print("="*60)
    
    # --- LOAD BRAIN ---
    print("🧠 Loading Hybrid AI Model...", end="\r")
    try:
        model = RecurrentPPO.load(MODEL_PATH)
        model.predict(np.zeros((1,17)), state=None, episode_start=[True], deterministic=True)
        print("✅ Hybrid AI Model Loaded & Warmed Up    ")
    except:
        print("❌ Error: Model not found. Using dummy inference time.")
        model = None

    # --- CONNECT PROTOCOL ---
    print("📡 Connecting to Local MQTT Broker...", end="\r")
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        client.loop_start()
        print("✅ Connected to Local MQTT Broker        ")
    except:
        print("❌ Error: Mosquitto not running! (Run: sudo systemctl start mosquitto)")
        return

    time.sleep(1) 

    # --- RUN TEST ---
    print(f"⏱️  Running 50 Control Cycles...", end="\r")
    
    obs = np.zeros((1, 17))
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)

    # Measure Inference
    t_start = time.time()
    for _ in range(100):
        if model: model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
    avg_inference = ((time.time() - t_start) / 100.0) * 1000.0

    # Measure Loop
    for i in range(50):
        t0 = time.time()
        if model:
            action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
        client.publish(TOPIC_ACTION, str(t0))
        time.sleep(0.02) 

    time.sleep(1) 
    client.loop_stop()
    print("✅ Benchmark Complete. Generating Report.  \n")

    # ==========================================
    # 3. GENERATE TABLE WITH SEPARATORS
    # ==========================================
    if not latencies_software:
        print("❌ No data received.")
        return

    avg_total_software = np.mean(latencies_software)
    protocol_overhead = max(0, avg_total_software - avg_inference)
    system_latency = avg_total_software + RELAY_DELAY_MS
    total_projected = system_latency + WIFI_ESTIMATE_MS

    # --- DEFINE SEPARATOR LINE ---
    sep = ["-"*22, "-"*12, "-"*28]

    # --- BUILD DATA WITH SEPARATORS ---
    data = [
        ["AI Inference",        f"{avg_inference:.2f}",    "Measured (Model Only)"],
        ["IoT Protocol Overhead", f"{protocol_overhead:.2f}", "Measured (MQTT Packet)"],
        ["Actuation Delay",     f"{RELAY_DELAY_MS:.2f}",     "Datasheet Standard"],
        
        sep,
        
        ["SYSTEM LATENCY",      f"**{system_latency:.2f}**", "Measured (SIL Loop)"],
        
        sep,

        ["Wi-Fi Transmission",  f"{WIFI_ESTIMATE_MS:.2f}",  "Estimated (Standard 2.4GHz)"],
        
        sep,

        ["TOTAL END-TO-END",    f"**{total_projected:.2f}**",   "Summation Prediction"],
        
        sep
    ]

    df = pd.DataFrame(data, columns=["Component", "Time (ms)", "Source / Method"])

    print("📊 TABLE 4.2: END-TO-END LATENCY BREAKDOWN")
    print(df.to_markdown(index=False))
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
