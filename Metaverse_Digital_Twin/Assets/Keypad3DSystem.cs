using UnityEngine;
using TMPro; // Keep this if using TextMeshPro

public class Keypad3DSystem : MonoBehaviour
{
    [Header("3D Display")]
    public TextMeshPro screenText; 

    [Header("Settings")]
    public string correctPin = "1234";
    private string currentInput = "";
    
    [Header("References")]
    // CHANGE 1: Use your actual script name here!
    public SmartDeviceController doorMqtt; 

    void Start()
    {
        UpdateScreen();
    }

    public void PressButton(string value)
    {
        if (value != "Enter" && value != "Clear")
        {
            if (currentInput.Length < 4)
            {
                currentInput += value;
                // Optional: Sound effect here
            }
        }
        else if (value == "Clear")
        {
            currentInput = "";
        }
        else if (value == "Enter")
        {
            CheckPin();
            return; 
        }

        UpdateScreen();
    }

    void CheckPin()
    {
        if (currentInput == correctPin)
        {
            screenText.text = "OPEN";
            screenText.color = Color.green;
            Debug.Log("ACCESS GRANTED");

            // CHANGE 2: Call the function inside SmartDeviceController
            if (doorMqtt != null)
            {
                // This sends {"state": "ON"} to the topic set in your Inspector
                doorMqtt.SendOnCommand(); 
            }
            
            Invoke("ResetKeypad", 2.0f);
        }
        else
        {
            screenText.text = "ERR";
            screenText.color = Color.red;
            currentInput = "";
            Invoke("UpdateScreen", 1.0f); 
        }
    }

    void ResetKeypad()
    {
        currentInput = "";
        screenText.color = Color.white; 
        UpdateScreen();
    }

    void UpdateScreen()
    {
        string stars = "";
        for(int i=0; i<currentInput.Length; i++) stars += "*";
        
        if(currentInput == "") screenText.text = "PIN...";
        else screenText.text = stars;
    }
}