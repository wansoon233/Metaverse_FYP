using UnityEngine;

public class PhysicalSwitch : MonoBehaviour
{
    [Header("Link to your Master Controller")]
    // 1. Changed this to exactly match your script name!
    public MasterSwitchController mainController; 

    // This is a built-in Unity function that detects when a mouse clicks a 3D Collider
    void OnMouseDown()
    {
        Debug.Log("Physical 3D Switch Clicked!");
        
        // Check if the controller is linked, then run your Toggle function
        if (mainController != null)
        {
            // 2. This calls the exact same function your 2D iPad button uses
            mainController.ToggleMasterSwitch(); 
        }
        else
        {
            Debug.LogError("MasterSwitchController not linked to the 3D Door Switch!");
        }
    }
}