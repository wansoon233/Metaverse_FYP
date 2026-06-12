using UnityEngine;
using Unity.Cinemachine;

public class FPSLook : MonoBehaviour
{
    [Header("References")]
    public Transform playerBody;   // still needed so movement follows look direction

    [Header("Sensitivity")]
    public float sensitivityX = 1.5f;
    public float sensitivityY = 1.5f;

    [Header("Vertical Clamp")]
    public float minPitch = -60f;
    public float maxPitch =  60f;

    // Store both angles ourselves — no longer rely on playerBody for yaw
    private float currentPitch = 0f;
    private float currentYaw   = 0f;

    private CinemachineBrain cinemachineBrain;

    void Start()
    {
        cinemachineBrain = GetComponent<CinemachineBrain>();
        if (cinemachineBrain != null)
            cinemachineBrain.enabled = false;

        // Start yaw from wherever the capsule is already facing
        currentYaw   = playerBody.eulerAngles.y;
        currentPitch = 0f;
    }

    public void OnLook(Vector2 delta)
    {
        currentYaw   += delta.x * sensitivityX;
        currentPitch -= delta.y * sensitivityY;
        currentPitch  = Mathf.Clamp(currentPitch, minPitch, maxPitch);

        // Rotate the whole capsule body left/right (camera follows as child)
        playerBody.rotation = Quaternion.Euler(0f, currentYaw, 0f);

        // Only tilt the camera up/down locally
        transform.localRotation = Quaternion.Euler(currentPitch, 0f, 0f);
    }

    public void EnableCinemachine(bool state)
    {
        if (cinemachineBrain != null)
            cinemachineBrain.enabled = state;
    }
}