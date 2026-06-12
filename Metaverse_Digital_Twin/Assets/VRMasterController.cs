using UnityEngine;

public class VRMasterController : MonoBehaviour
{
    public GameObject vrDashboard; 
    public Transform vrCamera; 
    public float distanceInFront = 1.2f;

    void Update()
    {
        // BUTTON C (Button 2) -> Toggle Hologram Menu
        if (Input.GetKeyDown(KeyCode.JoystickButton2)) 
        {
            if (vrDashboard != null)
            {
                bool isCurrentlyOn = vrDashboard.activeSelf;
                vrDashboard.SetActive(!isCurrentlyOn);

                if (!isCurrentlyOn)
                {
                    vrDashboard.transform.position = vrCamera.position + (vrCamera.forward * distanceInFront);
                    vrDashboard.transform.rotation = vrCamera.rotation;
                }
            }
        }
    }
}