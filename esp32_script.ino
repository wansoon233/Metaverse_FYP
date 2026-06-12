#include <WiFi.h>
#include <WiFiMulti.h> 
#include <PubSubClient.h>
#include <Wire.h>
#include "Adafruit_SHT31.h"
#include <esp_task_wdt.h> 

// ==========================================
// 1. SETTINGS & MQTT TOPICS
// ==========================================
#define WDT_TIMEOUT 15 // 15 Seconds until forced reboot if frozen

WiFiMulti wifiMulti; 
const char* mqtt_server = "192.168.0.18"; 
const float SYSTEM_VOLTAGE = 12.0; 

const char* topic_indoor_temp = "home/livingroom/temperature";
const char* topic_indoor_hum = "home/livingroom/humidity";
const char* topic_outdoor_temp = "home/outdoor/temperature";
const char* topic_outdoor_hum = "home/outdoor/humidity";
const char* topic_ac_power = "home/energy/ac_watts";
const char* topic_heater_power = "home/energy/heater_watts";

// ==========================================
// 2. PINS, SENSORS & TRACKERS
// ==========================================
WiFiClient espClient;
PubSubClient client(espClient);

Adafruit_SHT31 sht_indoor = Adafruit_SHT31();            
Adafruit_SHT31 sht_outdoor = Adafruit_SHT31(&Wire1);   

#define SDA_2 32
#define SCL_2 33
#define ACS_HEATER_PIN 34
#define ACS_AC_PIN 35
#define LED_PIN 2

unsigned long lastMsg = 0;
unsigned long lastReconnectAttempt = 0; 

unsigned long lastPingTime = 0;
int pingSequence = 0; 

// ==========================================
// 3. POWER CALCULATION FUNCTION 
// ==========================================
float getPowerInWatts(int pin) {
  int rawValue = analogRead(pin);
  float voltage = (rawValue / 4095.0) * 3.3;
  float v_drop = abs(2.5 - voltage); 
  if (v_drop < 0.05) { v_drop = 0.0; }
  float amps = v_drop / 0.100; 
  float watts = amps * SYSTEM_VOLTAGE;
  return watts;
}

// ==========================================
// 4. SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  Serial.println("\n--- Starting Master System ---");

  // Arm the Watchdog Time Bomb!
  Serial.println("Arming Watchdog Timer...");
  
  esp_task_wdt_config_t wdt_config;
  wdt_config.timeout_ms = WDT_TIMEOUT * 1000; // Convert 15 seconds to 15000 ms
  wdt_config.idle_core_mask = (1 << portNUM_PROCESSORS) - 1; // Watch all cores
  wdt_config.trigger_panic = true; // Force reboot on freeze
  
  esp_task_wdt_init(&wdt_config);
  esp_task_wdt_add(NULL); // Watch the main loop

  // I2C Setup with Timeout protection
  Wire.begin();
  Wire.setTimeOut(150); 
  if (!sht_indoor.begin(0x44)) {
    Serial.println("⚠️ Indoor sensor not found!");
  }

  Wire1.begin(SDA_2, SCL_2); 
  Wire1.setTimeOut(150);
  if (!sht_outdoor.begin(0x44)) {
    Serial.println("⚠️ Outdoor sensor not found!");
  }

  // WiFi Setup
  wifiMulti.addAP("Siow WiFi", "18739553");          
  wifiMulti.addAP("A-11-07","KKX996241107"); 
  wifiMulti.addAP("别点我的iPhone😵‍💫", "Sws12345");  
  
  Serial.println("Connecting to WiFi...");
  while (wifiMulti.run() != WL_CONNECTED) {
    esp_task_wdt_reset(); // Keep dog fed while connecting
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi Connected!");
  
  client.setServer(mqtt_server, 1883);
  client.setBufferSize(512); 
}

void reconnect() {
  Serial.println("Attempting MQTT connection...");
  String clientId = "ESP32Master-" + String(random(0xffff), HEX);
  
  if (client.connect(clientId.c_str())) {
    Serial.println("MQTT Connected!");
    client.publish("home/status", "Master ESP32 Online");
  } else {
    Serial.print("MQTT Connect failed, rc=");
    Serial.println(client.state());
  }
}

// ==========================================
// 5. MAIN LOOP
// ==========================================
void loop() {
  // Feed the Watchdog!
  esp_task_wdt_reset(); 

  // Non-blocking WiFi & MQTT Reconnect
  if (wifiMulti.run() == WL_CONNECTED) {
    if (!client.connected()) {
      unsigned long now = millis();
      if (now - lastReconnectAttempt > 5000) { 
        lastReconnectAttempt = now;
        reconnect();
      }
    } else {
      client.loop(); 
    }
  }

  yield(); 

  unsigned long now = millis();

  // ---------------------------------------------------------
  // 🕒 BLOCK 1: TELEMETRY (Runs every 3 seconds)
  // ---------------------------------------------------------
  if (now - lastMsg > 3000) {
    lastMsg = now;
    digitalWrite(LED_PIN, HIGH); // Turn LED on while processing

    // I2C Reads (The Danger Zone)
    float in_t = sht_indoor.readTemperature();
    float in_h = sht_indoor.readHumidity(); 
    
    float out_t = sht_outdoor.readTemperature();
    float out_h = sht_outdoor.readHumidity(); 
    
    float heater_watts = getPowerInWatts(ACS_HEATER_PIN);
    float ac_watts = getPowerInWatts(ACS_AC_PIN);

    if (client.connected()) {
        char buffer[10];
        
        if (!isnan(in_t)) {
          dtostrf(in_t, 1, 2, buffer);
          client.publish(topic_indoor_temp, buffer);
        }
        if (!isnan(in_h)) {
          dtostrf(in_h, 1, 2, buffer);
          client.publish(topic_indoor_hum, buffer);
        }
        if (!isnan(out_t)) {
          dtostrf(out_t, 1, 2, buffer);
          client.publish(topic_outdoor_temp, buffer);
        }
        if (!isnan(out_h)) {
          dtostrf(out_h, 1, 2, buffer);
          client.publish(topic_outdoor_hum, buffer);
        }

        dtostrf(heater_watts, 1, 2, buffer);
        client.publish(topic_heater_power, buffer);
        
        dtostrf(ac_watts, 1, 2, buffer);
        client.publish(topic_ac_power, buffer);
    }

    Serial.print("🏠 IN: "); Serial.print(in_t); Serial.print("°C | "); Serial.print(in_h); Serial.println("%");
    Serial.print("🌤️ OUT: "); Serial.print(out_t); Serial.print("°C | "); Serial.print(out_h); Serial.println("%");
    Serial.print("🔥 Heater: "); Serial.print(heater_watts); Serial.print(" W | ❄️ AC: "); Serial.print(ac_watts); Serial.println(" W");
    Serial.println("---------------------------------------");

    delay(100);
    digitalWrite(LED_PIN, LOW); // Safe! Turn LED off.
  }

  // ---------------------------------------------------------
  // 📡 BLOCK 2: NETWORK STRESS TEST PING (Runs every 10 seconds)
  // ---------------------------------------------------------
  if (now - lastPingTime >= 10000) {
    lastPingTime = now;
    pingSequence++;

    if (client.connected()) {
      // Build the JSON: {"ts": 123.45, "seq": 1}
      String payload = "{\"ts\":" + String(now / 1000.0) + ", \"seq\":" + String(pingSequence) + "}";
      
      client.publish("home/network/ping", payload.c_str());
      Serial.println("📡 QoS Ping Sent: Sequence #" + String(pingSequence));
    }
  }
}
