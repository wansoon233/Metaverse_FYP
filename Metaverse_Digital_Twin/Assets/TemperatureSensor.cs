using UnityEngine;
using TMPro; 
using M2MqttUnity;
using uPLibrary.Networking.M2Mqtt.Messages;
using System.Globalization;

[RequireComponent(typeof(AudioSource))]
public class TemperatureSensor : M2MqttUnityClient
{
    [Header("MQTT Wildcard Subscription")]
    public string baseTopic = "home/#"; 
    
    [Header("UI & Master Hub Connection")]
    public StatsManager statsManager; 
    public TextMeshProUGUI humText; 
    public TextMeshProUGUI tempText; 

    [Header("Fire Safety System")]
    public float fireThreshold = 45.0f; 
    public string alarmTopic = "home/safety/alarm";
    public AudioSource sirenAudio; 

    [Header("Emergency Cooling Devices")]
    public SmartDeviceController emergencyFan;
    public SmartDeviceController emergencyWindow;

    // --- SENSOR TRACKERS ---
    private string lastInTemp = "--", lastInHum = "--";
    private string lastOutTemp = "--", lastOutHum = "--";
    
    // ⚡ EDGE COMPUTING ENERGY TRACKERS
    private float latestKwh = 0f;
    private float latestFee = 0f;
    private bool updateEnergyUI = false;
    
    private bool updateUI = false;
    private bool isAlarmRinging = false; 

    protected override void Start()
    {
        base.Start(); 
        if (sirenAudio == null) sirenAudio = GetComponent<AudioSource>();
    }

    protected override void OnConnected()
    {
        base.OnConnected();
        client.Subscribe(new string[] { baseTopic }, new byte[] { MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE });
    }

    protected override void DecodeMessage(string topic, byte[] message)
    {
        string msg = System.Text.Encoding.UTF8.GetString(message);
        string lowerTopic = topic.ToLower();

        // 🚨 THE ENGINEERING FIX: Read the smoothed data from the Pi's AC payload!
        if (lowerTopic.Contains("livingroom/ac"))
        {
            try
            {
                AcPayload payload = JsonUtility.FromJson<AcPayload>(msg);
                
                // Grab the smoothed values and format them to 2 decimal places
                lastInTemp = payload.temp.ToString("F2", CultureInfo.InvariantCulture);
                lastInHum = payload.hum.ToString("F2", CultureInfo.InvariantCulture);
                lastOutTemp = payload.out_temp.ToString("F2", CultureInfo.InvariantCulture);
                lastOutHum = payload.out_hum.ToString("F2", CultureInfo.InvariantCulture);
                
                updateUI = true;
            }
            catch { Debug.LogWarning("Failed to parse incoming AC JSON for environment data."); }
        }
        
        // ⚡ CATCH THE TNB BILL DIRECTLY FROM THE PI
        else if (lowerTopic.Contains("system/energy"))
        {
            try
            {
                EnergyPayload payload = JsonUtility.FromJson<EnergyPayload>(msg);
                latestKwh = payload.kwh;
                latestFee = payload.fee;
                updateEnergyUI = true; 
            }
            catch { Debug.LogWarning("Failed to parse incoming energy JSON."); }
        }
        
        // 🤖 CATCH THE AI'S ACTIONS FROM THE PI
        else if (lowerTopic.Contains("system/action_log"))
        {
            string[] parts = msg.Split('"');
            if (parts.Length >= 8 && statsManager != null)
            {
                string piActor = parts[3];   
                string piAction = parts[7];  
                statsManager.LogAction(piActor, piAction); 
            }
        }
    }

    protected override void Update()
    {
        base.Update(); 

        // 1. UPDATE ENVIRONMENT UI
        if (updateUI)
        {
            if (humText != null) humText.text = "Hum: " + lastInHum + "%";
            if (tempText != null) tempText.text = "Temp: " + lastInTemp + "°C";

            // Parse Weather
            float inT = 24.0f, inH = 50.0f, outT = 24.0f, outH = 50.0f;
            float.TryParse(lastInTemp, NumberStyles.Any, CultureInfo.InvariantCulture, out inT);
            float.TryParse(lastInHum, NumberStyles.Any, CultureInfo.InvariantCulture, out inH);
            float.TryParse(lastOutTemp, NumberStyles.Any, CultureInfo.InvariantCulture, out outT);
            float.TryParse(lastOutHum, NumberStyles.Any, CultureInfo.InvariantCulture, out outH);

            if (statsManager != null) 
            {
                statsManager.UpdateEnvironment(inT, inH, outT, outH);
            }

            // 🔥 FIRE ALARM LOGIC
            if (inT >= fireThreshold && !isAlarmRinging) TriggerFireAlarm();
            else if (inT < fireThreshold && isAlarmRinging) StopFireAlarm();

            updateUI = false;
        }

        // 2. UPDATE ENERGY UI FROM THE EDGE SERVER (PI)
        if (updateEnergyUI)
        {
            if (statsManager != null)
            {
                statsManager.UpdateEnergyFromPi(latestKwh, latestFee);
            }
            updateEnergyUI = false;
        }
    }

    private void TriggerFireAlarm()
    {
        isAlarmRinging = true;
        Debug.LogError("🔥 FIRE ALARM! Venting smoke now!");
        if (sirenAudio != null && !sirenAudio.isPlaying) sirenAudio.Play();
        if (emergencyWindow != null) emergencyWindow.SendOnCommand();
        if (emergencyFan != null) emergencyFan.OnSliderChanged(3f);
        if (client != null && client.IsConnected) client.Publish(alarmTopic, System.Text.Encoding.UTF8.GetBytes("FIRE_DETECTED"), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
    }

    private void StopFireAlarm()
    {
        isAlarmRinging = false;
        Debug.Log("✅ Temperature stabilized. Alarm cleared.");
        if (sirenAudio != null) sirenAudio.Stop();
        if (client != null && client.IsConnected) client.Publish(alarmTopic, System.Text.Encoding.UTF8.GetBytes("ALARM_CLEARED"), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
    }

    // ⚡ Helper class for Energy JSON
    [System.Serializable]
    public class EnergyPayload
    {
        public float kwh;
        public float fee;
    }

    // 🚨 NEW: Helper class for AC/Environment JSON
    [System.Serializable]
    public class AcPayload
    {
        public string speed;
        public string ac_state;
        public string mode;
        public float temp;
        public float hum;
        public float out_temp;
        public float out_hum;
    }
}