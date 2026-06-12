using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class AIManager : MonoBehaviour
{
    public static AIManager instance; 

    [Header("UI Components")]
    public TextMeshProUGUI modeText;
    public Image backgroundPanel; 

    [Header("Colors")]
    public Color activeColor = new Color(0, 0.8f, 0); // Nice Green
    public Color standbyColor = new Color(0.8f, 0.6f, 0); // Nice Orange/Yellow

    void Awake()
    {
        instance = this; 
    }

    void Start()
    {
        // 🧠 MEMORY CHECK: Load the last known AI status from our save file!
        if (PlayerPrefs.HasKey("SavedAIStatus"))
        {
            bool lastKnownState = PlayerPrefs.GetInt("SavedAIStatus") == 1;
            
            // Instantly update the UI colors before the screen even fully loads
            SetAIStatus(lastKnownState); 
            Debug.Log("🧠 Loaded previous AI Status: " + (lastKnownState ? "ON" : "OFF"));
        }
    }

    // 🪄 The Pi will call this function to update the VR Dashboard!
    public void SetAIStatus(bool isAIActive)
    {
        // 💾 SAVE TO MEMORY: Whenever the Pi changes the status, save it forever!
        PlayerPrefs.SetInt("SavedAIStatus", isAIActive ? 1 : 0);
        PlayerPrefs.Save();

        if (isAIActive)
        {
            if (modeText != null) modeText.text = "AI STATUS: ON";
            if (backgroundPanel != null) backgroundPanel.color = activeColor;
        }
        else
        {
            if (modeText != null) modeText.text = "AI STATUS: OFF";
            if (backgroundPanel != null) backgroundPanel.color = standbyColor;
        }
    }
}