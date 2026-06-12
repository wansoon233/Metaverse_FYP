using UnityEngine;

public class SmartFanController : MonoBehaviour
{
    [Header("Fan Visual Settings")]
    public float maxSpeed = 800f;       // Top speed (100%)
    public float acceleration = 300f;   // How smoothly it accelerates
    public Vector3 rotationAxis = new Vector3(0, 1, 0); // Y-axis spin

    private float currentSpeed = 0f;
    private float targetSpeed = 0f;

    // This function will be called by our Slider script
    public void SetVisualSpeed(int speedLevel)
    {
        if (speedLevel == 0) targetSpeed = 0f;                          // OFF
        else if (speedLevel == 1) targetSpeed = maxSpeed * 0.33f;       // LOW
        else if (speedLevel == 2) targetSpeed = maxSpeed * 0.66f;       // MEDIUM
        else if (speedLevel == 3) targetSpeed = maxSpeed;               // HIGH
    }

    void Update()
    {
        // Smoothly calculate momentum
        currentSpeed = Mathf.MoveTowards(currentSpeed, targetSpeed, acceleration * Time.deltaTime);

        // Spin the 3D object
        if (currentSpeed > 0.1f)
        {
            transform.Rotate(rotationAxis, currentSpeed * Time.deltaTime);
        }
    }
}