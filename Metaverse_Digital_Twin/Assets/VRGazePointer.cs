using UnityEngine;

public class VRGazePointer : MonoBehaviour
{
    [Header("Mode Control")]
    public GameObject vrRig; 
    public AIManager aiManager; // Left this here so your Unity Inspector doesn't break!

    [Header("The Floating Dot")]
    public Transform reticle; 
    public float maxDistance = 5.0f;

    [Header("Dot Size Control")]
    public bool keepConstantVisualSize = true;
    public float baseSize = 0.05f;

    private Camera cam;

    void Start()
    {
        cam = GetComponent<Camera>();
    }

    void Update()
    {
        if (vrRig == null || !vrRig.activeInHierarchy)
        {
            if (reticle != null) reticle.gameObject.SetActive(false);
            return;
        }

        if (reticle != null && !reticle.gameObject.activeInHierarchy) 
        {
            reticle.gameObject.SetActive(true);
        }

        if (reticle == null) return;

        // 1. Raycast Every Frame
        Ray ray = new Ray(cam.transform.position, cam.transform.forward);
        RaycastHit hit;
        bool isLookingAtSomething = Physics.Raycast(ray, out hit, maxDistance);

        if (isLookingAtSomething)
        {
            reticle.position = hit.point;
        }
        else
        {
            reticle.position = cam.transform.position + cam.transform.forward * 2.0f;
        }

        // 2. --- INSTANT INPUT LOGIC ---
        // 🪄 The timer is gone! This now clicks instantly on Button 3 or Mouse Click.
        if (Input.GetKeyDown(KeyCode.JoystickButton3) || Input.GetMouseButtonDown(0)) 
        {
            if (isLookingAtSomething)
            {
                if (hit.collider.CompareTag("Interactable"))
                {
                    ExecuteShortPress(hit); // Run your custom device logic instantly
                }
            }
        }

        // 3. Dot Size Math
        if (keepConstantVisualSize)
        {
            float distance = Vector3.Distance(cam.transform.position, reticle.position);
            reticle.localScale = new Vector3(baseSize * distance, baseSize * distance, baseSize * distance);
        }
        else
        {
            reticle.localScale = new Vector3(baseSize, baseSize, baseSize);
        }
    }

    // 🪄 YOUR SPECIFIC DEVICE LOGIC IS SAFELY STORED HERE
    private void ExecuteShortPress(RaycastHit hit)
    {
        // Action A: Try to click a 3D Smart Home Device
        Interactable3DObject device = hit.collider.GetComponent<Interactable3DObject>();
        if (device != null && device.smartController != null)
        {
            if (device.isMultiSpeed && device.smartController.uiMultiSpeeds != null && device.smartController.uiMultiSpeeds.Length > 0)
            {
                device.smartController.uiMultiSpeeds[0].CycleSpeed();
            }
            else
            {
                device.smartController.ToggleDevice();
            }
        }
        
        // Action B: Try to click a UI Button on your Hologram Dashboard
        UnityEngine.UI.Button uiBtn = hit.collider.GetComponent<UnityEngine.UI.Button>();
        if (uiBtn != null)
        {
            uiBtn.onClick.Invoke();
        }
    }
}