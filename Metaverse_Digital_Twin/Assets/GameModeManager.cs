using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem; 
#endif

public class GameModeManager : MonoBehaviour
{
    [Header("Player Rigs")]
    public GameObject pcRig; // 👈 Drag your Capsule here
    public GameObject vrRig; // 👈 Drag your VR_Rig here

    [Header("Menu UI")]
    public GameObject mainMenuCanvas; // 👈 Drag your PC Dashboard/Menu here
    public GameObject vrDashboard; // 🪄 NEW: Drag your VR_Dashboard Canvas here!

    // This tracks which mode you are currently in!
    private bool isVRActive = false; 

    void Start()
    {
        // 🛡️ SAFETY FIRST: Always boot into PC mode so the tablet joysticks load safely!
        Debug.Log("Booting into safe PC Mode.");
        LaunchPCMode();
    }

    void Update()
    {
        // Safe keyboard checks for the New Input System (mostly for when you test on your laptop)
        #if ENABLE_INPUT_SYSTEM
        if (Keyboard.current != null)
        {
            if (Keyboard.current.mKey.wasPressedThisFrame || Keyboard.current.escapeKey.wasPressedThisFrame)
            {
                ShowMainMenu();
            }
        }
        #else
        // Backup old input system check
        if (Input.GetKeyDown(KeyCode.M) || Input.GetKeyDown(KeyCode.Escape))
        {
            ShowMainMenu();
        }
        #endif
    }

    // 🚪 --- THE ESCAPE HATCH --- 🚪
    // We will connect this exact function to your UI Button!
    public void ToggleVRMode()
    {
        isVRActive = !isVRActive; // Flips between true and false
        
        if (isVRActive)
        {
            LaunchVRMode();
        }
        else
        {
            LaunchPCMode();
        }
    }

    public void LaunchPCMode()
    {
        isVRActive = false;
        
        // Turn ON the Capsule, Turn OFF the VR Rig
        if (pcRig != null) pcRig.SetActive(true);
        if (vrRig != null) vrRig.SetActive(false);
        
        // Keep your IoT Dashboard/UI ON so you can tap the buttons
        if (mainMenuCanvas != null) mainMenuCanvas.SetActive(true); 

        // 🪄 NEW: Force the VR Hologram menu to close when leaving VR Mode!
        if (vrDashboard != null) vrDashboard.SetActive(false);
    }

    public void LaunchVRMode()
    {
        isVRActive = true;
        
        // Turn ON the VR Rig, Turn OFF the Capsule
        if (vrRig != null) vrRig.SetActive(true);
        if (pcRig != null) pcRig.SetActive(false);
        
        // Turn OFF the 2D Dashboard (Because standard UI looks glitchy inside VR lenses anyway)
        if (mainMenuCanvas != null) mainMenuCanvas.SetActive(false); 
    }

    public void ShowMainMenu()
    {
        if (pcRig != null) pcRig.SetActive(false);
        if (vrRig != null) vrRig.SetActive(false);
        if (mainMenuCanvas != null) mainMenuCanvas.SetActive(true);

        // 🪄 NEW: Also hide the VR dashboard if we hit the Master Escape Key
        if (vrDashboard != null) vrDashboard.SetActive(false);

        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }
}