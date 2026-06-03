import sys
import json
import time
import os
import numpy as np
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import requests  
import threading 
from RPLCD.i2c import CharLCD
from sb3_contrib import RecurrentPPO 

# 🚨 PMV Comfort Library 
try:
    from pythermalcomfort.models import pmv_ppd_iso
    PMV_READY = True
except ImportError:
    print("⚠️ pythermalcomfort not installed! Run: pip install pythermalcomfort")
    PMV_READY = False

# 🚨 NEW: Bulletproof PMV Fallback Function
def get_robust_pmv(temp, hum):
    if not PMV_READY: return 0.0
    try:
        val = pmv_ppd_iso(tdb=temp, tr=temp, vr=0.1, rh=hum, met=1.0, clo=0.5).pmv
        if np.isnan(val) or "nan" in str(val).lower():
            return 3.0 if temp >= 27.0 else -3.0
        return float(val)
    except:
        # If the library crashes due to extreme temps, force clamp it
        return 3.0 if temp >= 27.0 else -3.0

# ==========================================
# 1. PIN & TOPIC CONFIGURATION
# ==========================================
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

RELAY_MAP = {
    "home/livingroom/heater": 12, 
    "home/main/lock": 10, 
    "home/livingroom/peltier": 38
}

MOSFET_MAP = {"home/livingroom/fan": 16} 

LED_MAP = {
    "home/bathroom/light": 23, "home/room2/light": 21,
    "home/dining/light": 19, "home/room1/light": 18, "home/kitchen/light": 15
}

PIN_WINDOW_SERVO = 11  
PIN_ALARM        = 7    # Active Low Buzzer
PIN_DOOR_SERVO   = 40  

DOOR_LOCK_PWM = 7.5   
DOOR_UNLOCK_PWM = 5.5  

# GLOBAL VARIABLES
door_is_unlocked = False
unlock_start_time = 0
door_servo_reset = False 

current_temp = 24.0
current_hum = 50.0
in_temp_history = [24.0, 24.0, 24.0, 24.0] 

current_out_temp = 24.0
current_out_hum = 50.0

last_lcd_update = 0
alarm_active = False 
away_mode = False 

ai_is_active = True 
last_ai_time = 0 
last_human_interaction = time.time() 

current_ac_status = "OFF"
current_fan_status = "OFF"
current_heater_status = "OFF"

# 🚨 Clock Drift Memory
clock_drift_offset = None  

fan_pwm = None; servo = None; door_servo = None; client = None

topic_debounce = {}
def is_spam(topic):
    global topic_debounce
    now = time.time()
    if topic in topic_debounce and (now - topic_debounce[topic] < 0.5):
        topic_debounce[topic] = now
        return True
    topic_debounce[topic] = now
    return False

# ==========================================
# 📡 RELIABILITY TRACKERS & ENERGY
# ==========================================
ping_sequence = 0
expected_sequence = 0
total_lost_packets = 0

last_health_temp = 24.0
last_temp_change_time = time.time()

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdo74EEZFkB9Fwexiacw6wcn5VOeOp9tXQpMDfPO2f8mDPQxw/formResponse"

ENTRY_LOG_TYPE   = "entry.1483963513"
ENTRY_ACTOR      = "entry.1595242576"
ENTRY_MODE       = "entry.690806295"
ENTRY_IN_TEMP    = "entry.609354649"
ENTRY_IN_HUM     = "entry.1206087790" 
ENTRY_OUT_TEMP   = "entry.1517622145"
ENTRY_OUT_HUM    = "entry.317270067" 
ENTRY_ENERGY     = "entry.1898850716"
ENTRY_FEE        = "entry.257261320"
ENTRY_ACTION     = "entry.670802581"
ENTRY_PMV        = "entry.686217604" 
ENTRY_LATENCY    = "entry.1803086970" 
ENTRY_SETPOINT   = "entry.1665908567" 

total_monthly_kwh = 0.0
energy_file = "/home/wansoon/fyp_metaverse/energy_memory.json"

if os.path.exists(energy_file):
    try:
        with open(energy_file, "r") as f:
            total_monthly_kwh = json.load(f).get("kwh", 0.0)
        print(f"📊 Loaded Previous Energy Bill: {total_monthly_kwh:.4f} kWh")
    except: pass

def calculate_tnb_fee(kwh):
    cost = 0.0; remaining = kwh
    if remaining > 0: b = min(remaining, 200.0); cost += b * 0.218; remaining -= b
    if remaining > 0: b = min(remaining, 100.0); cost += b * 0.334; remaining -= b
    if remaining > 0: b = min(remaining, 300.0); cost += b * 0.516; remaining -= b
    if remaining > 0: b = min(remaining, 300.0); cost += b * 0.546; remaining -= b
    if remaining > 0: cost += remaining * 0.571
    return cost

def background_edge_loop():
    global total_monthly_kwh, current_ac_status, current_heater_status, door_is_unlocked, ping_sequence
    last_energy_time = time.time()
    last_env_log_time = time.time()
    
    while True:
        time.sleep(2.0) 
        now = time.time()
        
        hours_passed = (now - last_energy_time) / 3600.0
        last_energy_time = now
        
        active_watts = 0.0
        if current_ac_status == "ON": active_watts += 1000.0  
        if current_heater_status == "ON": active_watts += 1500.0
        
        for pin in LED_MAP.values():
            if GPIO.input(pin) == GPIO.HIGH: active_watts += 10.0 
                
        if not door_is_unlocked: active_watts += 5.0

        if active_watts > 0:
            total_monthly_kwh += (active_watts / 1000.0) * hours_passed
            with open(energy_file, "w") as f: json.dump({"kwh": total_monthly_kwh}, f)
            
            if client:
                current_fee = calculate_tnb_fee(total_monthly_kwh)
                client.publish("home/system/energy", json.dumps({"kwh": total_monthly_kwh, "fee": current_fee}))

        if now - last_env_log_time >= 60.0:
            last_env_log_time = now
            write_pi_log("ENVIRONMENT", "Sensors", "-")

def send_to_google_cloud(log_type, actor, details, in_t, in_h, out_t, out_h, energy_str, fee_str, pmv_str, latency_str, interface_mode, setpoint_str):
    form_data = {
        ENTRY_LOG_TYPE: log_type,        
        ENTRY_ACTOR: actor,            
        ENTRY_MODE: interface_mode,    
        ENTRY_IN_TEMP: in_t,          
        ENTRY_IN_HUM: in_h,
        ENTRY_OUT_TEMP: out_t,             
        ENTRY_OUT_HUM: out_h,
        ENTRY_ENERGY: energy_str,            
        ENTRY_FEE: fee_str,                  
        ENTRY_ACTION: details,
        ENTRY_PMV: pmv_str,
        ENTRY_SETPOINT: setpoint_str,
        ENTRY_LATENCY: latency_str
    }
    try:
        requests.post(GOOGLE_FORM_URL, data=form_data, timeout=5)
    except Exception as e: pass

def write_pi_log(log_type, actor, details, interface="PI_HARDWARE", latency_ms="-", ai_setpoint="-"):
    global current_temp, current_hum, current_out_temp, current_out_hum, total_monthly_kwh
    csv_file = "/home/wansoon/fyp_metaverse/pi_hardware_log.csv"
    time_str = time.strftime("%Y-%m-%d %H:%M:%S")
    
    in_t = f"{current_temp:.2f}"
    in_h = f"{current_hum:.2f}"
    out_t = f"{current_out_temp:.2f}"
    out_h = f"{current_out_hum:.2f}"
    
    energy_str = f"{total_monthly_kwh:.4f}"
    fee_str = f"{calculate_tnb_fee(total_monthly_kwh):.4f}"
    
    # 🚨 Using the new robust PMV function
    pmv_val = get_robust_pmv(current_temp, current_hum)
    pmv_str = f"{pmv_val:+.2f}" if PMV_READY else "-"

    if latency_ms != "-": latency_str = str(latency_ms)
    else: latency_str = "-"
    
    csv_row = f"{time_str},{log_type},{actor},{interface},{in_t},{in_h},{out_t},{out_h},{energy_str},{fee_str},{details},{pmv_str},{ai_setpoint},{latency_str}\n"
    
    if not os.path.exists(csv_file):
        with open(csv_file, "w") as file:
            file.write("Timestamp,Log Type,Actor,Interface Mode,Indoor Temp,Indoor Humidity,Outdoor Temp,Outdoor Humidity,Energy (kWh),Fee (RM),Action,PMV,AI Setpoint,Latency (ms)\n")
            
    with open(csv_file, "a") as file: file.write(csv_row)
    
    threading.Thread(target=send_to_google_cloud, args=(log_type, actor, details, in_t, in_h, out_t, out_h, energy_str, fee_str, pmv_str, latency_str, interface, ai_setpoint), daemon=True).start()

# ==========================================
# 2. AI BRAIN CLASSES
# ==========================================
class SmartShield:
    def get_safety_action(self, current_temp):
        if current_temp > 25.8: return 24.0
        elif current_temp < 23.2: return 28.0
        return 26.0

class MetaverseHybridBrain:
    def __init__(self, model_name="ppo_lstm.zip"):
        print("Loading LSTM-PPO Brain...")
        paths_to_try = [model_name, os.path.join("models", "Hybrid", "saved_models", model_name)]
        self.model = None
        for path in paths_to_try:
            try:
                self.model = RecurrentPPO.load(path)
                print(f"   [OK] Brain Loaded from: {path}")
                break
            except: pass
        if not self.model: print(f"   [ERROR] Could not find {model_name}!")
        self.shield = SmartShield()
        self.lstm_states = None
        self.episode_starts = np.ones((1,), dtype=bool)

    def get_hvac_action(self, obs_array):
        if not self.model: return 26.0, 20.0, "ERROR"
        obs = np.array([obs_array], dtype=np.float32)
        temp = obs[0][9]

        if temp < 23.2 or temp > 25.8:
            target_cooling = self.shield.get_safety_action(temp)
            target_heating = 24.0 
            mode = "SHIELD_ACTIVE"
            _, self.lstm_states = self.model.predict(obs, state=self.lstm_states, episode_start=self.episode_starts, deterministic=True)
        else:
            action, self.lstm_states = self.model.predict(obs, state=self.lstm_states, episode_start=self.episode_starts, deterministic=True)
            
            val_heat = np.clip(action[0][0], -1.0, 1.0)
            val_cool = np.clip(action[0][1], -1.0, 1.0)
            
            target_heating = 12.0 + (0.5 * (val_heat + 1.0) * (23.25 - 12.0))
            target_cooling = 23.5 + (0.5 * (val_cool + 1.0) * (30.0 - 23.5))
            mode = "LSTM_AI"
            
        self.episode_starts = np.zeros((1,), dtype=bool)
        return target_cooling, target_heating, mode

ai_brain = MetaverseHybridBrain("ppo_lstm.zip")

# ==========================================
# 3. HARDWARE SETUP
# ==========================================
try:
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)
    lcd.clear()
    lcd.write_string("SYSTEM BOOT...")
    time.sleep(1) 
    lcd.clear()
except:
    print("LCD NOT DETECTED")
    lcd = None

def lcd_print(line1, line2=""):
    if lcd:
        try:
            lcd.cursor_pos = (0, 0); lcd.write_string(line1.ljust(16)[:16]) 
            lcd.cursor_pos = (1, 0); lcd.write_string(line2.ljust(16)[:16])
        except: pass

def force_relay_off(pin): 
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)

def force_relay_on(pin): 
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def setup_hardware():
    print("Configuring Hardware...")
    global fan_pwm, servo, door_servo
    
    for pin in RELAY_MAP.values(): force_relay_off(pin)
    for pin in MOSFET_MAP.values(): GPIO.setup(pin, GPIO.OUT); GPIO.output(pin, GPIO.LOW)
    
    fan_pwm = GPIO.PWM(MOSFET_MAP["home/livingroom/fan"], 1000); fan_pwm.start(0)
    for pin in LED_MAP.values(): GPIO.setup(pin, GPIO.OUT); GPIO.output(pin, GPIO.LOW)
    
    # 🚨 Active Low Buzzer Setup (Starts HIGH = Silent)
    GPIO.setup(PIN_ALARM, GPIO.OUT)
    GPIO.output(PIN_ALARM, GPIO.HIGH)
    
    GPIO.setup(PIN_WINDOW_SERVO, GPIO.OUT); servo = GPIO.PWM(PIN_WINDOW_SERVO, 50); servo.start(0)
    GPIO.setup(PIN_DOOR_SERVO, GPIO.OUT); door_servo = GPIO.PWM(PIN_DOOR_SERVO, 50); door_servo.start(0)

# ==========================================
# 4. CONTROL FUNCTIONS
# ==========================================
def trigger_buzzer(make_sound):
    """Standard Active Low Output Logic."""
    if make_sound:
        GPIO.output(PIN_ALARM, GPIO.LOW)  # BEEP
    else:
        GPIO.output(PIN_ALARM, GPIO.HIGH) # SILENCE

def control_hvac(name, pin, status):
    global current_heater_status, current_ac_status
    if status in ["ON", "HIGH", "TRUE"]:
        force_relay_on(pin)
        if "peltier" in name.lower(): current_ac_status = "ON"
        if "heater" in name.lower(): current_heater_status = "ON"
    else:
        force_relay_off(pin)
        if "peltier" in name.lower(): current_ac_status = "OFF"
        if "heater" in name.lower(): current_heater_status = "OFF"
    print(f"[*] {name} is {status}")

def control_mosfet(name, pwm_obj, command):
    global current_fan_status
    cmd_str = str(command).upper()
    duty_cycle = 0; status = "OFF"
    
    if cmd_str in ["OFF", "0", "FALSE"]: duty_cycle = 0; status = "OFF"
    elif cmd_str in ["LOW", "1"]: duty_cycle = 30; status = "LOW"
    elif cmd_str in ["MEDIUM", "MED", "2"]: duty_cycle = 70; status = "MEDIUM"
    elif cmd_str in ["HIGH", "ON", "TRUE", "3"]: duty_cycle = 100; status = "HIGH"
    
    current_fan_status = status
    print(f"[*] {name} set to {status} ({duty_cycle}%)")
    
    if duty_cycle > 0: pwm_obj.ChangeDutyCycle(100); time.sleep(0.1)
    pwm_obj.ChangeDutyCycle(duty_cycle)

def control_led(name, pin, status):
    if status in ["ON", "TRUE", "HIGH"]: GPIO.output(pin, GPIO.HIGH)
    else: GPIO.output(pin, GPIO.LOW)

def trigger_unlock():
    global door_is_unlocked, unlock_start_time, door_servo_reset
    if door_is_unlocked: return 
    print("UNLOCKING DOOR...")
    force_relay_on(RELAY_MAP["home/main/lock"]); time.sleep(0.1) 
    door_servo.ChangeDutyCycle(DOOR_UNLOCK_PWM); time.sleep(0.3); door_servo.ChangeDutyCycle(0)
    
    door_is_unlocked = True; unlock_start_time = time.time(); door_servo_reset = False 
    if client: client.publish("home/main/lock", json.dumps({"state": "ON", "mode": "PI_HARDWARE", "ts": time.time() * 1000}))

def trigger_lock():
    global door_is_unlocked, door_servo_reset
    if not door_is_unlocked: return 
    print("LOCKING DOOR...")
    
    if not door_servo_reset:
        door_servo.ChangeDutyCycle(DOOR_LOCK_PWM); time.sleep(0.3); door_servo.ChangeDutyCycle(0)
        door_servo_reset = True

    force_relay_off(RELAY_MAP["home/main/lock"]); door_is_unlocked = False
    if client: client.publish("home/main/lock", json.dumps({"state": "OFF", "mode": "PI_HARDWARE", "ts": time.time() * 1000}))

def set_window(status):
    print(f"[*] WINDOW is {status}")
    if status in ["ON", "OPEN", "TRUE"]: servo.ChangeDutyCycle(7.5) 
    else: servo.ChangeDutyCycle(2.5)
    time.sleep(1.0); servo.ChangeDutyCycle(0)

def check_temperature_alarm(temp_val):
    global alarm_active
    if temp_val > 37.0:
        if not alarm_active:
            print(f"🚨 FIRE ALARM! Temp is {temp_val}C! Opening Window & Fan!")
            trigger_buzzer(True) 
            control_mosfet("AC Fan", fan_pwm, "HIGH"); set_window("OPEN"); alarm_active = True
            write_pi_log("ACTION", "SYSTEM ALARM", "FIRE DETECTED - Windows Opened")
    else:
        if alarm_active:
            print(f"✅ Temp Normal ({temp_val}C). Fire Alarm OFF.")
            trigger_buzzer(False) 
            control_mosfet("AC Fan", fan_pwm, "OFF"); set_window("CLOSE"); alarm_active = False
            write_pi_log("ACTION", "SYSTEM ALARM", "Normal Temp Restored")

def activate_away_mode():
    global ai_is_active, away_mode
    print("\n🌙 AWAY MODE ACTIVATED: Shutting down entire house...")
    ai_is_active = False; away_mode = True      
    
    control_hvac("AC Peltier", RELAY_MAP["home/livingroom/peltier"], "OFF")
    control_mosfet("AC Fan", fan_pwm, "OFF")
    control_hvac("HEATER", RELAY_MAP["home/livingroom/heater"], "OFF")
    
    for name, pin in LED_MAP.items(): control_led(name.split("/")[-2].upper() + " LIGHT", pin, "OFF")
    set_window("CLOSE"); trigger_lock(); lcd_print("AWAY MODE", "Power Saving ON")
    trigger_buzzer(False) 
    write_pi_log("ACTION", "USER", "Activated AWAY Mode")

    if client:
        client.publish("home/system/master", "OFF", retain=True)
        client.publish("home/system/mode", "MANUAL", retain=True)
        client.publish("home/livingroom/ac", json.dumps({
            "speed": "OFF", 
            "ac_state": "OFF",
            "mode": "MANUAL",
            "temp": round(current_temp, 2),
            "hum": round(current_hum, 2),
            "out_temp": round(current_out_temp, 2),
            "out_hum": round(current_out_hum, 2),
            "setpoint": "-"
        }))
        client.publish("home/livingroom/heater", '{"state": "OFF"}')
        client.publish("home/main/lock", json.dumps({"state": "OFF", "mode": "PI_HARDWARE", "ts": time.time() * 1000}))
        client.publish("home/livingroom/window", '{"state": "OFF"}')
        for name in LED_MAP.keys(): client.publish(name, '{"state": "OFF"}')

# ==========================================
# 5. AI ENGINE
# ==========================================
def run_ai_routine(temp_val):
    global last_ai_time, ai_is_active

    if time.time() - last_ai_time < 3.0: return
    last_ai_time = time.time()

    if not ai_is_active or away_mode:
        if client: 
            client.publish("home/livingroom/ac", json.dumps({
                "speed": current_fan_status, 
                "ac_state": current_ac_status, 
                "mode": "AWAY" if away_mode else "MANUAL", 
                "temp": round(temp_val, 2),
                "hum": round(current_hum, 2),
                "out_temp": round(current_out_temp, 2),
                "out_hum": round(current_out_hum, 2),
                "setpoint": "-"
            }))
        return
        
    start_processing_time = time.time()
        
    # 1. Get the target from the Deep Learning LSTM
    obs = np.zeros(17); obs[9] = temp_val
    target_cool, target_heat, mode = ai_brain.get_hvac_action(obs)
    
    # 2. 🚨 THE SMARTER LOGIC: Using the robust PMV fallback
    current_pmv = get_robust_pmv(temp_val, current_hum)

    temp_difference = temp_val - target_cool 
    
    # 3. 🧠 Hybrid Intelligence: Combine AI targets with PMV Comfort
    if current_pmv > 1.0 or temp_difference > 2.0: 
        # Human feels HOT or AI demands massive drop -> Panic Cool
        ac_cmd, fan_cmd = "ON", "HIGH"   
    elif current_pmv > 0.5 or temp_difference > 0.5: 
        # Human feels WARM or AI wants a steady drop -> Normal Cool
        ac_cmd, fan_cmd = "ON", "MEDIUM" 
    elif current_pmv >= -0.5 and current_pmv <= 0.5 and temp_difference <= 0.2:
        # 🏆 PERFECT COMFORT ZONE! Save TNB Bill. Just circulate air gently.
        ac_cmd, fan_cmd = "OFF", "LOW"
    else: 
        # Room is cool enough, shut it down.
        ac_cmd, fan_cmd = "OFF", "OFF"     

    # Only turn on heater if it's actually freezing cold (PMV < -1.0)
    heater_cmd = "ON" if temp_val < target_heat and current_pmv < -1.0 else "OFF"
    
    print(f"[AI] Room: {temp_val:.2f}C | Target: {target_cool:.2f}C | Diff: {temp_difference:+.2f}C | PMV: {current_pmv:+.2f} -> AC:{ac_cmd} FAN:{fan_cmd}")
    
    action_taken = False
    
    if fan_cmd != current_fan_status or ac_cmd != current_ac_status:
        control_hvac("AC Peltier", RELAY_MAP["home/livingroom/peltier"], ac_cmd)
        control_mosfet("AC Fan", fan_pwm, fan_cmd)
        action_taken = True
        
        latency_ms = (time.time() - start_processing_time) * 1000
        write_pi_log("ACTION", "LSTM_AI", f"Set AC Fan to {fan_cmd} & Peltier {ac_cmd}", latency_ms=f"{latency_ms:.1f}", ai_setpoint=f"{target_cool:.2f}")
        if client: client.publish("home/system/action_log", json.dumps({"actor": "LSTM_AI", "action": f"Set AC Fan to {fan_cmd}"}))
            
    if heater_cmd != current_heater_status:
        control_hvac("HEATER", RELAY_MAP["home/livingroom/heater"], heater_cmd)
        action_taken = True
        
        latency_ms = (time.time() - start_processing_time) * 1000
        write_pi_log("ACTION", "LSTM_AI", f"Turned Heater {heater_cmd}", latency_ms=f"{latency_ms:.1f}", ai_setpoint=f"{target_cool:.2f}")
        if client: client.publish("home/system/action_log", json.dumps({"actor": "LSTM_AI", "action": f"Turned Heater {heater_cmd}"}))

    if client: 
        try:
            client.publish("home/livingroom/ac", json.dumps({
                "speed": fan_cmd, 
                "ac_state": ac_cmd, 
                "mode": mode, 
                "temp": round(temp_val, 2),
                "hum": round(current_hum, 2),
                "out_temp": round(current_out_temp, 2),
                "out_hum": round(current_out_hum, 2),
                "setpoint": round(target_cool, 2)
            }))
            if action_taken:
                client.publish("home/livingroom/heater", json.dumps({"state": heater_cmd}))
        except Exception as e: pass

# ==========================================
# 6. MQTT LOGIC 
# ==========================================
def on_connect(mqtt_client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("MQTT Connected")
        mqtt_client.subscribe("home/#")

def on_message(mqtt_client, userdata, msg):
    global current_temp, current_hum, current_out_temp, current_out_hum, in_temp_history
    global ai_is_active, last_human_interaction, away_mode, clock_drift_offset
    
    try:
        topic = msg.topic.lower() 
        payload = msg.payload.decode("utf-8")
        
        if "energy" in topic or "watts" in topic or "log" in topic or "system/mode" in topic: return
        
        if "network/ping" in topic:
            try:
                data = json.loads(payload)
                recv_seq = data["seq"]
                
                global expected_sequence, total_lost_packets
                # Only calculate lost packets after the first sequence is established
                if expected_sequence > 0 and recv_seq > expected_sequence: 
                    total_lost_packets += abs(recv_seq - expected_sequence)
                expected_sequence = recv_seq + 1

                global last_health_temp, last_temp_change_time
                sensor_status = "OK"
                if current_temp != last_health_temp:
                    last_health_temp = current_temp; last_temp_change_time = time.time()
                elif (time.time() - last_temp_change_time) > 10800: sensor_status = "FROZEN_WARNING"

                health_csv = "/home/wansoon/fyp_metaverse/fyp_network_health.csv"
                time_str = time.strftime("%Y-%m-%d %H:%M:%S")
                
                row = f"{time_str},{total_lost_packets},{sensor_status}\n" 
                
                if not os.path.exists(health_csv):
                    with open(health_csv, "w") as f: f.write("Timestamp,Total Lost Packets,Sensor Health\n")
                with open(health_csv, "a") as f: f.write(row)
            except: pass
            return
            
        if "outdoor" in topic:
            if "temp" in topic or "temperature" in topic: current_out_temp = float(payload)
            if "hum" in topic or "humidity" in topic: current_out_hum = float(payload)
            return

        if "temp" in topic or "temperature" in topic:
            raw_temp = float(payload)
            
            if in_temp_history == [24.0, 24.0, 24.0, 24.0]:
                in_temp_history = [raw_temp, raw_temp, raw_temp, raw_temp]
            else:
                in_temp_history.append(raw_temp)
                if len(in_temp_history) > 4: in_temp_history.pop(0) 
                
            current_temp = sum(in_temp_history) / len(in_temp_history) 
            
            check_temperature_alarm(current_temp) 
            if not alarm_active: run_ai_routine(current_temp)
            return 

        if "hum" in topic or "humidity" in topic: current_hum = float(payload); return 

        if is_spam(topic): return

        tablet_timestamp = 0.0
        remote_mode = "PI_HARDWARE"
        command = payload
        calculated_latency_ms = "-"

        try:
            data = json.loads(payload)
            command = data.get("state", data.get("speed", data.get("value", payload)))
            if "ts" in data: tablet_timestamp = float(data["ts"])
            if "mode" in data: remote_mode = data["mode"]
        except: pass

        if tablet_timestamp > 0:
            pi_time_now = time.time() * 1000.0
            if clock_drift_offset is None:
                clock_drift_offset = (pi_time_now - tablet_timestamp) - 30.0
                print(f"\n[*] Calibrated Cross-OS Clock Drift: {clock_drift_offset:.1f}ms")
            
            true_latency = abs((pi_time_now - tablet_timestamp) - clock_drift_offset)
            calculated_latency_ms = f"{true_latency:.1f}"
        
        cmd_str = str(command).upper()
        
        if "system/master" in topic:
            if cmd_str in ["OFF", "FALSE", "0"]: 
                if not away_mode: activate_away_mode()
            else:
                if away_mode: 
                    print("\n🏠 HOME MODE ACTIVATED: Welcome back! Waking up AI...")
                    away_mode = False; ai_is_active = True
                    lcd_print("SYSTEM ONLINE", f"T:{current_temp:.2f}C")
                    write_pi_log("ACTION", "USER", "Activated HOME Mode", interface=remote_mode, latency_ms=calculated_latency_ms)
                    
                    if client: 
                        client.publish("home/system/master", "ON", retain=True)
                        client.publish("home/system/mode", "AUTO", retain=True)
            return

        if "ac" in topic or "fan" in topic:
            std_cmd = "OFF"
            if cmd_str in ["LOW", "1"]: std_cmd = "LOW"
            elif cmd_str in ["MEDIUM", "MED", "2"]: std_cmd = "MEDIUM"
            elif cmd_str in ["HIGH", "ON", "TRUE", "3"]: std_cmd = "HIGH"
        else:
            std_cmd = "OFF"
            if cmd_str in ["ON", "TRUE", "HIGH", "1"]: std_cmd = "ON"

        if "ac" in topic and std_cmd == current_fan_status: return
        if "heater" in topic and std_cmd == current_heater_status: return
        
        if "lock" in topic and std_cmd in ["ON","TRUE"] and door_is_unlocked: return
        if "lock" in topic and std_cmd in ["OFF", "FALSE"] and not door_is_unlocked: return
        
        if "ac" in topic or "fan" in topic or "heater" in topic or "light" in topic or "window" in topic:
            last_human_interaction = time.time()
            
            if ("ac" in topic or "heater" in topic or "fan" in topic) and ai_is_active:
                ai_is_active = False
                print(f"Human Override Detected! AI Sleeping. (Temp: {current_temp:.2f}C)")
                write_pi_log("ACTION", "SYSTEM", "Human Override Detected! AI Sleeping.")
                if client: client.publish("home/system/mode", "MANUAL")

        # Flip the hardware first...
        if "window" in topic: set_window(std_cmd)
        elif "lock" in topic: trigger_unlock() if std_cmd in ["ON", "TRUE"] else trigger_lock()
        else:
            if "ac" in topic:
                state = "OFF" if std_cmd == "OFF" else "ON"
                control_hvac("AC Peltier", RELAY_MAP["home/livingroom/peltier"], state)
                control_mosfet("AC Fan", fan_pwm, std_cmd)   
                
                if client: client.publish("home/livingroom/ac", json.dumps({
                    "speed": std_cmd, 
                    "ac_state": state, 
                    "mode": "MANUAL", 
                    "temp": round(current_temp, 2),
                    "hum": round(current_hum, 2),
                    "out_temp": round(current_out_temp, 2),
                    "out_hum": round(current_out_hum, 2),
                    "setpoint": "-"
                }))
            else:
                for key, pin in RELAY_MAP.items():
                    if key in topic: 
                        control_hvac(key.split("/")[-1].upper(), pin, std_cmd)
                        if client and "heater" in topic: client.publish("home/livingroom/heater", json.dumps({"state": std_cmd}))
                
                for key, pin in LED_MAP.items():
                    if key in topic: control_led(key.split("/")[-2].upper() + " LIGHT", pin, std_cmd)

        write_pi_log("ACTION", "USER", f"Set {topic.split('/')[-1].upper()} to {std_cmd}", interface=remote_mode, latency_ms=calculated_latency_ms)
                    
    except Exception as e: print(f"Error Parsing Message: {e}")

# ==========================================
# 7. MAIN EXECUTION
# ==========================================
setup_hardware()
write_pi_log("SYSTEM", "BOOT", "--- Raspberry Pi AI Master Started ---")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect("localhost", 1883, 60)
    client.loop_start()
    print("System Online. Ambient AI Active.")
    
    client.publish("home/system/master", "ON", retain=True)
    client.publish("home/system/mode", "AUTO", retain=True)

    threading.Thread(target=background_edge_loop, daemon=True).start()

    while True:
        if door_is_unlocked:
            elapsed_door_time = time.time() - unlock_start_time
            
            if elapsed_door_time > 3.0 and not door_servo_reset:
                print("[*] Soft-resetting Door Servo to prevent power spike...")
                step_size = (DOOR_UNLOCK_PWM - DOOR_LOCK_PWM) / 5.0
                current_pwm = DOOR_UNLOCK_PWM
                for _ in range(5):
                    current_pwm -= step_size
                    door_servo.ChangeDutyCycle(current_pwm)
                    time.sleep(0.05)
                time.sleep(0.1)
                door_servo.ChangeDutyCycle(0)   
                door_servo_reset = True
                
            if elapsed_door_time > 5.0: trigger_lock()

        if not ai_is_active and not away_mode and (time.time() - last_human_interaction > 15):
            print("Idle Timeout. Waking AI...")
            ai_is_active = True
            write_pi_log("ACTION", "SYSTEM", "Idle Timeout - AI Reactivated")
            if client: client.publish("home/system/mode", "AUTO")
            		
        if time.time() - last_lcd_update > 2.0:
            if alarm_active:
                lcd_print("!!! FIRE !!!", f"TEMP: {current_temp:.1f}C")
            elif not away_mode:
                mode_txt = "AUTO" if ai_is_active else "MANL"
                lcd_print(f"AI:{mode_txt} T:{current_temp:.2f}", f"H:{current_hum:.2f}")
            elif away_mode:
                lcd_print("AWAY MODE", "Power Saving ON")
            last_lcd_update = time.time()
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nSTOPPING")
    write_pi_log("SYSTEM", "SHUTDOWN", "Master Script Stopped Manually")
    if lcd: lcd.close(clear=True) 
    if servo: servo.stop()
    if door_servo: door_servo.stop()
    if fan_pwm: fan_pwm.stop()
    trigger_buzzer(False) 
    GPIO.cleanup()
    client.loop_stop()
