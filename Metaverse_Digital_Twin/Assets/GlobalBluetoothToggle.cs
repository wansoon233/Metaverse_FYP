using UnityEngine;

public class GlobalBluetoothToggle : MonoBehaviour
{
    public GameModeManager gameManager;
    
    // If B is Button 1, we listen for it here. Change this if your tester says otherwise!
    public KeyCode toggleButton = KeyCode.JoystickButton1; 

    void Update()
    {
        if (Input.GetKeyDown(toggleButton))
        {
            if (gameManager != null) gameManager.ToggleVRMode();
        }
    }
}