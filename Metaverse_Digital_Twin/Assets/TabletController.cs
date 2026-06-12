using UnityEngine;

public class TabletController : MonoBehaviour
{
    public GameObject    tabletMenu;
    public FullScreenSwipe swipeController;  // ← drag SwipeController here in Inspector

    public void ToggleTabletMenu()
    {
        Debug.Log("📱 Phone Icon Clicked!");

        if (tabletMenu == null)
        {
            Debug.LogError("🚨 ERROR: The Tablet Menu slot is empty in the UIManager!");
            return;
        }

        bool isCurrentlyOpen = tabletMenu.activeSelf;
        bool willOpen = !isCurrentlyOpen;

        tabletMenu.SetActive(willOpen);

        // Block camera look when dashboard opens, unblock when it closes
        if (swipeController != null)
        {
            if (willOpen)
                swipeController.BlockInput();
            else
                swipeController.UnblockInput();
        }

        Debug.Log("📱 Tablet is now: " + willOpen);
    }
}