using UnityEngine;
using TMPro;
using System.Collections;
using System.IO; 
using UnityEngine.Networking; 

public class StatsManager : MonoBehaviour
{
    [Header("☁️ Google Forms Cloud Sync")]
    public string cloudFormUrl = "https://docs.google.com/forms/d/e/1FAIpQLSdo74EEZFkB9Fwexiacw6wcn5VOeOp9tXQpMDfPO2f8mDPQxw/formResponse";
    
    public string entryLogType = "entry.1483963513";
    public string entryActor = "entry.1595242576";
    public string entryInterfaceMode = "entry.690806295";
    
    [Header("Environment Data IDs")]
    public string entryIndoorTemp = "entry.609354649"; 
    public string entryIndoorHumidity = "entry.1206087790";  
    public string entryOutdoorTemp = "entry.1517622145"; 
    public string entryOutdoorHumidity = "entry.317270067"; 
    
    [Header("System Data IDs")]
    public string entryEnergy = "entry.1898850716"; 
    public string entryFee = "entry.257261320";    
    public string entryAction = "entry.670802581"; 
    public string entryPmv = "entry.686217604";          
    public string entryLatency = "entry.1803086970";
    public string entrySetpoint = "entry.1665908567";        

    [Header("UI Text References")]
    public TMP_Text[] tempTexts;
    public TMP_Text[] kwhTexts;
    public TMP_Text[] feeTexts;

    [Header("Application State")]
    public string currentInterfaceMode = "Tablet"; 
    
    public string currentSystemMode = "HOME"; // Defaults to HOME
    public bool isAwayMode = false;

    private string csvFilePath;

    // We store these separately now so the UI knows what to log
    private string lastKnownInTempStr = "-";
    private string lastKnownInHumidStr = "-";
    private string lastKnownOutTempStr = "-";
    private string lastKnownOutHumidStr = "-";
    private string lastKnownEnergyStr = "0.0000";
    private string lastKnownFeeStr = "0.0000";
    // 🚨 NEW: Tracking the last known setpoint from the Pi
    private string lastKnownSetpointStr = "-";

    void Start()
    {
        csvFilePath = Application.persistentDataPath + "/Secret_System_Log.csv";
        if (!File.Exists(csvFilePath))
        {
            File.AppendAllText(csvFilePath, "Timestamp,Log Type,Actor,Interface Mode,System Mode,Indoor Temp,Indoor Humidity,Outdoor Temp,Outdoor Humidity,Energy (kWh),Fee (RM),Action,PMV,AI Setpoint,Latency (ms)\n");
        }
        File.AppendAllText(csvFilePath, $"\n,,,,,,,,,,,,,,--- NEW SESSION STARTED ({currentInterfaceMode} MODE) ---\n");
    }

    public void SetInterfaceMode(string newMode)
    {
        currentInterfaceMode = newMode.ToUpper();
    }

    public void SetSystemMode(string mode)
    {
        currentSystemMode = mode.ToUpper();
        if (currentSystemMode == "AWAY") 
        {
            isAwayMode = true;
            Debug.Log("StatsManager: System is now in AWAY mode.");
        }
        else 
        {
            isAwayMode = false;
            Debug.Log("StatsManager: System is now in HOME mode.");
        }
    }

    // ====================================================================
    // 📡 RECEIVING DATA FROM THE PI
    // ====================================================================
    public void UpdateEnvironment(float newInT, float newInH, float newOutT, float newOutH)
    {
        lastKnownInTempStr = newInT.ToString("F2");
        lastKnownInHumidStr = newInH.ToString("F2");
        
        lastKnownOutTempStr = newOutT.ToString("F2");
        lastKnownOutHumidStr = newOutH.ToString("F2");

        foreach (var t in tempTexts) { if (t != null) t.text = newInT.ToString("F2"); }
    }

    public void UpdateEnergyFromPi(float kwh, float fee)
    {
        lastKnownEnergyStr = kwh.ToString("F4");
        lastKnownFeeStr = fee.ToString("F4");

        foreach (var k in kwhTexts) { if (k != null) k.text = lastKnownEnergyStr + " kWh"; }
        foreach (var f in feeTexts) { if (f != null) f.text = "RM " + lastKnownFeeStr; }
    }

    public void UpdateSetpointFromPi(float setpoint)
    {
        lastKnownSetpointStr = setpoint.ToString("F2");
    }

    // ====================================================================
    // 📝 THE MAIN ACTION LOGGER (USER CLICKS ONLY)
    // ====================================================================
    public void LogAction(string actor, string action)
    {
        if (actor != "USER") return;

        string timestamp = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        string pmvStr = "-";
        string latencyStr = "-";
        
        // 🚨 NEW: Added lastKnownSetpointStr to the local CSV log
        File.AppendAllText(csvFilePath, $"{timestamp},ACTION,{actor},{currentInterfaceMode},{currentSystemMode},{lastKnownInTempStr},{lastKnownInHumidStr},{lastKnownOutTempStr},{lastKnownOutHumidStr},{lastKnownEnergyStr},{lastKnownFeeStr},{action},{pmvStr},{lastKnownSetpointStr},{latencyStr}\n"); 

        // 🚨 NEW: Added lastKnownSetpointStr to the Cloud coroutine parameters
        // StartCoroutine(PostToCloud("ACTION", actor, currentInterfaceMode, lastKnownInTempStr, lastKnownInHumidStr, lastKnownOutTempStr, lastKnownOutHumidStr, lastKnownEnergyStr, lastKnownFeeStr, action, pmvStr, lastKnownSetpointStr, latencyStr));
    }

    // ====================================================================
    // 🎮 2D DASHBOARD HELPERS
    // ====================================================================
    public void LogUserActionFromUI(string whatDidTheUserDo) { LogAction("USER", whatDidTheUserDo); }

    public void LogAcSpeed(float speedValue)
    {
        int speed = Mathf.RoundToInt(speedValue);
        string speedName = "UNKNOWN";

        if (speed == 0) speedName = "OFF";
        else if (speed == 1) speedName = "LOW";
        else if (speed == 2) speedName = "MEDIUM";
        else if (speed == 3) speedName = "HIGH";

        LogAction("USER", "Set AC Speed to " + speedName);
    }

    // ====================================================================
    // 🚀 THE CLOUD WEBHOOK
    // ====================================================================
    IEnumerator PostToCloud(string logType, string actor, string mode, string inTempStr, string inHumidStr, string outTempStr, string outHumidStr, string energyStr, string feeStr, string actionStr, string pmvStr, string setpointStr, string latencyStr)
    {
        WWWForm form = new WWWForm();
        form.AddField(entryLogType, logType);
        form.AddField(entryActor, actor);
        form.AddField(entryInterfaceMode, mode);
        
        form.AddField(entryIndoorTemp, inTempStr);
        form.AddField(entryIndoorHumidity, inHumidStr);
        form.AddField(entryOutdoorTemp, outTempStr);
        form.AddField(entryOutdoorHumidity, outHumidStr);
        
        form.AddField(entryEnergy, energyStr); 
        form.AddField(entryFee, feeStr);       
        form.AddField(entryAction, actionStr);
        form.AddField(entryPmv, pmvStr);
        form.AddField(entryLatency, latencyStr);
        form.AddField(entrySetpoint, setpointStr);

        using (UnityWebRequest www = UnityWebRequest.Post(cloudFormUrl, form))
        {
            // The disguise mask!
            www.SetRequestHeader("User-Agent", "Mozilla/5.0 (Windows NT) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36");
            yield return www.SendWebRequest();
        }
    }
}