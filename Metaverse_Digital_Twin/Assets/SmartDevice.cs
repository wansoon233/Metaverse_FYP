using UnityEngine;
using UnityEngine.UI;
using M2MqttUnity;
using uPLibrary.Networking.M2Mqtt.Messages;
using System.Collections; 

public class SmartDeviceController : M2MqttUnityClient
{
    [Header("Device Settings")]
    public string topic = "home/device/control"; 
    public bool isAutoLockDoor = false; 
    public float autoLockTime = 5f;
    private Coroutine autoLockTimer; 

    [Header("1. Simple Controls")]
    public Button btnOn;
    public Button btnOff;

    [Header("2. Slider Controls")]
    public Slider deviceSlider;

    [Header("3. Visual Effects")]
    public SmartFanController visualFan;
    public SmartACVisuals visualAC;
    public SmartLightVisuals visualLight;
    public SmartDoorVisuals visualDoor;
    public SmartHeaterVisuals visualHeater;
    public SmartWindowVisuals visualWindow;

    [Header("4. Two-Way UI Sync")]
    public DeviceToggle[] uiToggles; 
    public MultiSpeedDevice[] uiMultiSpeeds; 

    private bool isCurrentlyOn = false;
    private int currentSpeedLevel = -1; 

    // --- HARDWARE TRACKERS ---
    private bool hasNewMessage = false;
    private string incomingState = "";
    private int incomingSpeed = -1;

    // --- AI SYSTEM TRACKERS ---
    private bool hasNewModeMessage = false;
    private string incomingMode = "";

    protected override void Start()
    {
        base.Start(); 
        if (btnOn != null) btnOn.onClick.AddListener(SendOnCommand);
        if (btnOff != null) btnOff.onClick.AddListener(SendOffCommand);
        if (deviceSlider != null) 
        {
            deviceSlider.wholeNumbers = true;
            deviceSlider.onValueChanged.AddListener(OnSliderChanged);
        }
    }

    // ==========================================
    // 1. SEND COMMANDS TO PI (WITH TIMESTAMP!)
    // ==========================================
    public void SendOnCommand() { PublishNetworkMessage("ON"); }
    public void SendOffCommand() { PublishNetworkMessage("OFF"); }
    
    public void ToggleDevice()
    {
        if (isCurrentlyOn) SendOffCommand(); else SendOnCommand();  
    }

    public void OnSliderChanged(float value)
    {
        int speedLevel = (int)value;
        string stateMsg = "OFF";
        if (speedLevel == 1) stateMsg = "LOW";
        else if (speedLevel == 2) stateMsg = "MEDIUM";
        else if (speedLevel == 3) stateMsg = "HIGH";

        PublishNetworkMessage(stateMsg, speedLevel);
    }

    private void PublishNetworkMessage(string stateValue, int passedSpeed = -1)
    {
        if (client != null && client.IsConnected)
        {
            StatsManager stats = FindFirstObjectByType<StatsManager>();
            string mode = (stats != null) ? stats.currentInterfaceMode : "TABLET";

            string ts = System.DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString();
            string jsonPayload = "{\"state\": \"" + stateValue + "\", \"ts\": " + ts + ", \"mode\": \"" + mode + "\"}";
            
            // 🚨 FIX: QoS dropped to AT_MOST_ONCE to heavily reduce network latency times
            client.Publish(topic, System.Text.Encoding.UTF8.GetBytes(jsonPayload), MqttMsgBase.QOS_LEVEL_AT_MOST_ONCE, false);
            
            SyncVisualsOnly(stateValue, passedSpeed);
        }
    }

    // ==========================================
    // 2. RECEIVE MESSAGES FROM PI
    // ==========================================
    protected override void OnConnected()
    {
        base.OnConnected();
        client.Subscribe(new string[] { topic, "home/system/mode" }, new byte[] { MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE });
    }

    protected override void DecodeMessage(string msgTopic, byte[] message)
    {
        string msg = System.Text.Encoding.UTF8.GetString(message);
        
        if (msgTopic == topic)
        {
            if (msg.Contains("\"speed\": \"HIGH\"") || msg.Contains("\"state\": \"HIGH\"") || msg.Contains("\"3\"")) { incomingState = "HIGH"; incomingSpeed = 3; }
            else if (msg.Contains("\"speed\": \"MEDIUM\"") || msg.Contains("\"state\": \"MEDIUM\"") || msg.Contains("\"2\"")) { incomingState = "MEDIUM"; incomingSpeed = 2; }
            else if (msg.Contains("\"speed\": \"LOW\"") || msg.Contains("\"state\": \"LOW\"") || msg.Contains("\"1\"")) { incomingState = "LOW"; incomingSpeed = 1; }
            else if (msg.Contains("\"speed\": \"OFF\"") || msg.Contains("\"state\": \"OFF\"")) { incomingState = "OFF"; incomingSpeed = 0; }
            else if (msg.Contains("\"state\": \"ON\"") || msg.Contains("\"ON\"")) { incomingState = "ON"; incomingSpeed = -1; }
            else if (msg.Contains("\"OFF\"")) { incomingState = "OFF"; incomingSpeed = 0; } 

            hasNewMessage = true; 
        }
        else if (msgTopic == "home/system/mode")
        {
            if (msg.Contains("AUTO")) incomingMode = "AUTO";
            else if (msg.Contains("MANUAL")) incomingMode = "MANUAL";
            hasNewModeMessage = true; 
        }
    }

    protected override void Update()
    {
        base.Update();
        
        if (hasNewMessage)
        {
            hasNewMessage = false;
            SyncVisualsOnly(incomingState, incomingSpeed);
        }

        if (hasNewModeMessage)
        {
            hasNewModeMessage = false;
            if (incomingMode == "AUTO" && AIManager.instance != null) AIManager.instance.SetAIStatus(true);
            else if (incomingMode == "MANUAL" && AIManager.instance != null) AIManager.instance.SetAIStatus(false);
        }
    }

    // ==========================================
    // 3. SILENT UI UPDATE
    // ==========================================
    private void SyncVisualsOnly(string state, int speed = -1)
    {
        isCurrentlyOn = (state != "OFF");

        if (visualLight != null) visualLight.SetLightState(isCurrentlyOn);
        if (visualDoor != null) visualDoor.SetDoorState(isCurrentlyOn);
        if (visualHeater != null) visualHeater.SetHeaterState(isCurrentlyOn);
        if (visualWindow != null) visualWindow.SetWindowState(isCurrentlyOn);
        
        foreach(var t in uiToggles) { if (t != null) t.SyncUI(isCurrentlyOn); }

        if (speed >= 0 || deviceSlider != null)
        {
            currentSpeedLevel = speed >= 0 ? speed : (isCurrentlyOn ? 3 : 0);
            
            if (deviceSlider != null) deviceSlider.SetValueWithoutNotify(currentSpeedLevel);
            
            if (visualFan != null) visualFan.SetVisualSpeed(currentSpeedLevel);
            if (visualAC != null) visualAC.SetACSpeed(currentSpeedLevel);
            foreach(var m in uiMultiSpeeds) { if (m != null) m.SyncUI(currentSpeedLevel); }
        }
    }
}