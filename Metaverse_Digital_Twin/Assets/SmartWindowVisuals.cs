using UnityEngine;

public class SmartWindowVisuals : MonoBehaviour
{
    [Header("Window Push Settings")]
    [Tooltip("Change X, Y, or Z to 45 or -45 until it pushes the right way!")]
    public Vector3 openRotationOffset = new Vector3(45f, 0f, 0f);   
    public float swingSpeed = 5f;

    private Quaternion closedRotation;
    private Quaternion openRotation;
    private Quaternion targetRotation;

    void Start()
    {
        // Remember the closed position
        closedRotation = transform.localRotation;
        
        // This takes the current rotation and adds your custom X, Y, or Z offset!
        openRotation = Quaternion.Euler(transform.localEulerAngles + openRotationOffset);
        
        targetRotation = closedRotation; // Start closed
    }

    public void SetWindowState(bool isOpen)
    {
        if (isOpen) targetRotation = openRotation;
        else targetRotation = closedRotation;
    }

    void Update()
    {
        // Smoothly push the window to the target angle
        transform.localRotation = Quaternion.Slerp(transform.localRotation, targetRotation, Time.deltaTime * swingSpeed);
    }
}