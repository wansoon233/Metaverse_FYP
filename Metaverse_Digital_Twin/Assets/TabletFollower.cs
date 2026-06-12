using UnityEngine;

public class TabletFollower : MonoBehaviour
{
    [Tooltip("How far away it spawns when you open it")]
    public float distance = 18f;

    private Camera cam;

    void OnEnable()
    {
        cam = Camera.main;
        if (cam != null)
        {
            // 1. Teleport exactly in front of where you are looking right now
            Vector3 spawnPos = cam.transform.position + (cam.transform.forward * distance);
            spawnPos.y = cam.transform.position.y - 0.2f; 
            transform.position = spawnPos;
        }
    }

    void LateUpdate()
    {
        if (cam == null) return;

        // 2. Always rotate to face you, no matter where you move
        transform.LookAt(transform.position + cam.transform.rotation * Vector3.forward,
                         cam.transform.rotation * Vector3.up);
    }
}