using UnityEngine;

public class SmartDoorVisuals : MonoBehaviour
{
    [Header("Door Swing Settings")]
    public float openAngle = 90f;   // How far the door opens
    public float swingSpeed = 5f;   // How fast it swings

    private Quaternion closedRotation;
    private Quaternion openRotation;
    private Quaternion targetRotation;

    void Start()
    {
        // Remember exactly how the door is positioned when the game starts
        closedRotation = transform.localRotation;
        // Calculate what 90 degrees open looks like
        openRotation = Quaternion.Euler(transform.localEulerAngles.x, transform.localEulerAngles.y + openAngle, transform.localEulerAngles.z);
        
        targetRotation = closedRotation; // Start closed
    }

    public void SetDoorState(bool isOpen)
    {
        if (isOpen) targetRotation = openRotation;
        else targetRotation = closedRotation;
    }

    void Update()
    {
        // Smoothly rotate the door towards the target angle
        transform.localRotation = Quaternion.Slerp(transform.localRotation, targetRotation, Time.deltaTime * swingSpeed);
    }
}