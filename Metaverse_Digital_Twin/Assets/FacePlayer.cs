using UnityEngine;

public class FacePlayer : MonoBehaviour
{
    private Camera cam;

    void LateUpdate()
    {
        // If camera is null or disabled (during mode switch), find the new active one
        if (cam == null || !cam.gameObject.activeInHierarchy)
        {
            cam = Camera.main;
            if (cam == null) return; 
        }

        // Keep the UI flat and readable relative to the active camera
        transform.LookAt(transform.position + cam.transform.rotation * Vector3.forward,
                         cam.transform.rotation * Vector3.up);
    }
}