using UnityEngine;

public class VRGyroLook : MonoBehaviour
{
    void Start()
    {
        // Force the gyroscope ON, bypassing Huawei's hardware checks
        Input.gyro.enabled = true;
    }

    void Update()
    {
        // The mathematical conversion from Android hardware to Unity 3D space
        Quaternion deviceRotation = new Quaternion(Input.gyro.attitude.x, Input.gyro.attitude.y, -Input.gyro.attitude.z, -Input.gyro.attitude.w);
        
        // Apply the rotation
        transform.localRotation = Quaternion.Euler(90f, 0f, 0f) * deviceRotation;
    }
}