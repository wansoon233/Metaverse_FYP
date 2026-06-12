using UnityEngine;
using UnityEngine.UI;

public class DeviceToggle : MonoBehaviour
{
    [Header("UI Settings")]
    public Image statusIndicator;
    public Color onColor = Color.green;
    public Color offColor = Color.red;

    [Header("Cloud Logging")]
    [Tooltip("Type the device name here! (e.g., Heater, Light)")]
    public string deviceName = "Unknown Device";

    public SmartDeviceController smartController; 
    private bool isOn = false;

    // 1. This runs ONLY when you click the 2D Tablet Button
    public void ToggleDevice()
    {
        isOn = !isOn; 
        if (smartController != null)
        {
            if (isOn) smartController.SendOnCommand();
            else smartController.SendOffCommand();
        }

        // 📝 THE MAGIC LOGGING LINES! (Updated for modern Unity versions)
        string stateText = isOn ? "ON" : "OFF";
        
        StatsManager stats = FindFirstObjectByType<StatsManager>();
        if (stats != null)
        {
            stats.LogAction("USER", $"Turned {stateText} the {deviceName}");
        }
    }

    // 2. The Master Controller calls this to magically update the tablet colors!
    public void SyncUI(bool deviceState)
    {
        isOn = deviceState;
        if (statusIndicator != null) 
        {
            statusIndicator.color = isOn ? onColor : offColor;
        }
    }
}