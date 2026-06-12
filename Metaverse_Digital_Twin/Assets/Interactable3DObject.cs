using UnityEngine;

[RequireComponent(typeof(Collider))] 
public class Interactable3DObject : MonoBehaviour
{
    [Header("Master Controller")]
    public SmartDeviceController smartController;

    [Header("What kind of device is this?")]
    [Tooltip("Check this box for Fans and ACs. Leave unchecked for Lights and Heaters.")]
    public bool isMultiSpeed = false;

    void Start()
    {
        if (smartController == null)
        {
            smartController = GetComponent<SmartDeviceController>();
        }
    }

}