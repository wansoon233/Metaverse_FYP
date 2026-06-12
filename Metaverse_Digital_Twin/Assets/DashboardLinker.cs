using UnityEngine;

public class DashboardLinker : MonoBehaviour
{
    [Header("Drag the matching Canvas here")]
    public GameObject myDashboard;

    void Start()
    {
        // Ensure the dashboard is hidden when the game starts
        if (myDashboard != null)
        {
            myDashboard.SetActive(false);
        }
    }
}