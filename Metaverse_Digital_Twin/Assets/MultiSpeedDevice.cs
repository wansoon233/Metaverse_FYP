using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class MultiSpeedDevice : MonoBehaviour
{
    [Header("UI Settings")]
    public Image statusIndicator;
    public TextMeshProUGUI speedText;
    
    public Color offColor = Color.red;
    public Color speed1Color = new Color(0.6f, 1f, 0.6f);
    public Color speed2Color = new Color(0.2f, 0.8f, 0.2f);
    public Color speed3Color = new Color(0f, 0.5f, 0f);

    [Header("Cloud Logging")]
    [Tooltip("Type the device name here! (e.g., AC)")]
    public string deviceName = "AC";

    public SmartDeviceController smartController; 
    private int currentSpeed = 0;

    // 1. This runs ONLY when you click the 2D Tablet Button
    public void CycleSpeed()
    {
        currentSpeed++;
        if (currentSpeed > 3) currentSpeed = 0;

        if (smartController != null)
        {
            smartController.OnSliderChanged((float)currentSpeed); 
        }

        // 📝 THE MAGIC LOGGING LINES!
        // Convert the number into readable text for the Google Sheet
        string speedName = "UNKNOWN";
        if (currentSpeed == 0) speedName = "OFF";
        else if (currentSpeed == 1) speedName = "LOW";
        else if (currentSpeed == 2) speedName = "MEDIUM";
        else if (currentSpeed == 3) speedName = "HIGH";

        StatsManager stats = FindFirstObjectByType<StatsManager>();
        if (stats != null)
        {
            stats.LogAction("USER", $"Set {deviceName} Speed to {speedName}");
        }
    }

    // 2. The Master Controller calls this to magically update the tablet colors!
    public void SyncUI(int speed)
    {
        currentSpeed = speed;
        
        if (statusIndicator != null)
        {
            switch (currentSpeed)
            {
                case 0: statusIndicator.color = offColor; break;
                case 1: statusIndicator.color = speed1Color; break;
                case 2: statusIndicator.color = speed2Color; break;
                case 3: statusIndicator.color = speed3Color; break;
            }
        }
        if (speedText != null) speedText.text = currentSpeed == 0 ? "OFF" : "SPD " + currentSpeed;
    }
}