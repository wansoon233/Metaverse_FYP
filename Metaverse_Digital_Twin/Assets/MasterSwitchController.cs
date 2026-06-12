using UnityEngine;
using UnityEngine.UI;
using TMPro; 
using M2MqttUnity;
using uPLibrary.Networking.M2Mqtt.Messages;

public class MasterSwitchController : M2MqttUnityClient
{
    [Header("MQTT Settings")]
    public string masterTopic = "home/system/master";

    [Header("2D iPad UI")]
    public TMP_Text ipadButtonText; 
    public Image ipadButtonImage;          

    [Header("3D Wall Panel UI")]
    public Image wallHomeButtonImage;
    public Image wallAwayButtonImage;

    [Header("Other Devices (Force Update)")]
    public Image[] allDeviceIndicators; 
    
    [Header("3D Smart Lights")]
    public SmartLightVisuals[] allSmartLights; 

    [Header("Colors")]
    public Color activeHomeColor = new Color(0.2f, 0.6f, 1.0f); // Bright Blue
    public Color activeAwayColor = new Color(0.8f, 0.2f, 0.2f); // Bright Red
    public Color inactiveColor = new Color(0.3f, 0.3f, 0.3f);   // Dark Grey
    public Color lightOffColor = Color.red;                     // Red for turned-off UI devices

    private bool isAwayModeActive = false; 
    private bool hasNewNetworkState = false; // 🚨 Tracks if the Pi updated us

    protected override void Start()
    {
        base.Start(); 

        if (PlayerPrefs.HasKey("SavedAwayMode"))
        {
            isAwayModeActive = PlayerPrefs.GetInt("SavedAwayMode") == 1;
            Debug.Log("🧠 Loaded previous Mode State. Away Mode: " + isAwayModeActive);
        }

        UpdateButtonUI();
    }

    // ==========================================
    // 🎛️ BUTTON TRIGGERS (Talking to the Pi)
    // ==========================================
    public void ToggleMasterSwitch()
    {
        isAwayModeActive = !isAwayModeActive; 
        ExecuteStateChange();
    }

    public void SetHomeMode()
    {
        if (isAwayModeActive) 
        {
            isAwayModeActive = false;
            ExecuteStateChange();
        }
    }

    public void SetAwayMode()
    {
        if (!isAwayModeActive) 
        {
            isAwayModeActive = true;
            ExecuteStateChange();
        }
    }

    private void ExecuteStateChange()
    {
        // Save locally and send the command to the network
        PlayerPrefs.SetInt("SavedAwayMode", isAwayModeActive ? 1 : 0);
        PlayerPrefs.Save();

        if (isAwayModeActive)
        {
            Debug.Log("Shutting down the house...");
            PublishMessage("OFF"); 
        }
        else
        {
            Debug.Log("Waking up the AI...");
            PublishMessage("ON");  
        }

        StatsManager stats = FindFirstObjectByType<StatsManager>();
        if (stats != null)
        {
            // 🚨 Update StatsManager internal state BEFORE logging the action
            stats.SetSystemMode(isAwayModeActive ? "AWAY" : "HOME");
            
            string modeText = isAwayModeActive ? "Activated AWAY Mode" : "Activated HOME Mode";
            stats.LogAction("USER", modeText);
        }

        UpdateButtonUI();
    }

    private void PublishMessage(string message)
    {
        if (client != null && client.IsConnected)
        {
            client.Publish(masterTopic, System.Text.Encoding.UTF8.GetBytes(message), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
        }
    }

    // ==========================================
    // 📡 LISTENING TO THE PI
    // ==========================================
    protected override void OnConnected()
    {
        base.OnConnected();
        client.Subscribe(new string[] { masterTopic }, new byte[] { MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE });
    }

    protected override void DecodeMessage(string msgTopic, byte[] message)
    {
        string msg = System.Text.Encoding.UTF8.GetString(message).ToUpper();

        if (msgTopic == masterTopic)
        {
            if (msg.Contains("OFF") || msg.Contains("FALSE") || msg.Contains("0"))
            {
                isAwayModeActive = true;
            }
            else
            {
                isAwayModeActive = false;
            }
            
            hasNewNetworkState = true; 
        }
    }

    protected override void Update()
    {
        base.Update();
        
        if (hasNewNetworkState)
        {
            hasNewNetworkState = false;
            
            PlayerPrefs.SetInt("SavedAwayMode", isAwayModeActive ? 1 : 0);
            PlayerPrefs.Save();
            
            UpdateButtonUI();
        }
    }

    // ==========================================
    // 🎨 UI UPDATER
    // ==========================================
    private void UpdateButtonUI()
    {
        // 🚨 ADDED: Tell the StatsManager the current state so all future CSV logs know what mode the house is in!
        StatsManager stats = FindFirstObjectByType<StatsManager>();
        if (stats != null)
        {
            stats.SetSystemMode(isAwayModeActive ? "AWAY" : "HOME");
        }

        if (isAwayModeActive)
        {
            if (ipadButtonText != null) ipadButtonText.text = "SYSTEM: AWAY";
            if (ipadButtonImage != null) ipadButtonImage.color = activeAwayColor;

            if (wallAwayButtonImage != null) wallAwayButtonImage.color = activeAwayColor;
            if (wallHomeButtonImage != null) wallHomeButtonImage.color = inactiveColor;

            foreach (Image indicator in allDeviceIndicators)
            {
                if (indicator != null) indicator.color = lightOffColor;
            }

            foreach (SmartLightVisuals smartLight in allSmartLights)
            {
                if (smartLight != null) 
                {
                    smartLight.SetLightState(false); 
                }
            }
        }
        else
        {
            if (ipadButtonText != null) ipadButtonText.text = "SYSTEM: HOME";
            if (ipadButtonImage != null) ipadButtonImage.color = activeHomeColor;

            if (wallHomeButtonImage != null) wallHomeButtonImage.color = activeHomeColor;
            if (wallAwayButtonImage != null) wallAwayButtonImage.color = inactiveColor;
        }
    }
}