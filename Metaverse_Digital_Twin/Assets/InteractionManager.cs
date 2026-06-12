using UnityEngine;

public class InteractionManager : MonoBehaviour
{
    [Header("Settings")]
    public float interactDistance = 4.0f; // Distance set to 4 meters (Close range)
    
    private Camera cam;
    private DashboardLinker currentTarget; // The device we are currently looking at

    void Start()
    {
        cam = GetComponent<Camera>();
        if (cam == null) cam = Camera.main;
    }

    void Update()
    {
        // 1. If mouse is visible (we are clicking), do not close the menu.
        if (Cursor.visible) return;

        // 2. Prepare Laser
        Ray ray = cam.ViewportPointToRay(new Vector3(0.5f, 0.5f, 0));
        RaycastHit hit;

        // 3. Shoot Laser
        if (Physics.Raycast(ray, out hit, interactDistance))
        {
            // We hit something! Check if it has the "Linker" script.
            DashboardLinker hitLinker = hit.collider.GetComponent<DashboardLinker>();

            if (hitLinker != null)
            {
                // We are looking at a smart device!
                if (currentTarget != hitLinker)
                {
                    ChangeTarget(hitLinker);
                }
                return; // Stop here. We found a target.
            }
        }

        // 4. If we reach here, we are looking at a Wall or Air.
        // So, close the dashboard immediately.
        if (currentTarget != null)
        {
            CloseDashboard();
        }
    }

    // --- HELPER FUNCTIONS ---

    void ChangeTarget(DashboardLinker newTarget)
    {
        CloseDashboard(); 

        currentTarget = newTarget;
        if (currentTarget.myDashboard != null)
        {
            currentTarget.myDashboard.SetActive(true);
        }
    }

    void CloseDashboard()
    {
        if (currentTarget != null)
        {
            if (currentTarget.myDashboard != null)
            {
                currentTarget.myDashboard.SetActive(false);
            }
            currentTarget = null;
        }
    }
}