using UnityEngine;

public class SmartLightVisuals : MonoBehaviour
{
    [Header("1. The Actual Light Object")]
    public Light roomLight;

    [Header("2. The 3D Bulb Objects")]
    [Tooltip("You can drag 1, 2, or as many bulbs as you want into this list!")]
    public GameObject[] bulbObjects; // The [] turns this into a list!

    [Header("3. Materials")]
    [Tooltip("Drag the glowing material here")]
    public Material lightOnMaterial;

    [Tooltip("Drag a dark/unlit material here")]
    public Material lightOffMaterial;

    void Start()
    {
        SetLightState(false); 
    }

    public void SetLightState(bool isOn)
    {
        // 1. Turn the actual Unity Light invisible rays on/off
        if (roomLight != null)
        {
            roomLight.enabled = isOn; 
        }

        // 2. Safely swap the material of ALL 3D Square bulbs in the list
        if (bulbObjects != null && lightOnMaterial != null && lightOffMaterial != null)
        {
            // This 'foreach' loop goes through every single bulb you plugged in
            foreach (GameObject bulb in bulbObjects)
            {
                if (bulb != null)
                {
                    Renderer bulbRenderer = bulb.GetComponent<Renderer>();
                    
                    if (bulbRenderer != null)
                    {
                        bulbRenderer.material = isOn ? lightOnMaterial : lightOffMaterial;
                    }
                }
            }
        }
    }
}