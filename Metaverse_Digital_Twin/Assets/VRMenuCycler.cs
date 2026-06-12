using UnityEngine;
using UnityEngine.UI;

public class VRMenuCycler : MonoBehaviour
{
    [Header("Menu Setup")]
    public GameObject vrDashboard; 
    public Button[] dashboardButtons; 
    
    [Header("Auto-Scroll Setup")]
    public ScrollRect menuScrollRect; 
    [Tooltip("How many buttons can you see on the screen at the same time?")]
    public int visibleButtonsOnScreen = 4; // 🪄 NEW: This creates the deadzone!

    [Header("Colors to show selection")]
    public Color normalColor = Color.white;
    public Color highlightedColor = Color.yellow; 

    private int currentIndex = 0;

    void Update()
    {
        if (vrDashboard != null && vrDashboard.activeInHierarchy)
        {
            if (Input.GetKeyDown(KeyCode.JoystickButton0)) // Button B
            {
                CycleToNextButton();
            }

            if (Input.GetKeyDown(KeyCode.JoystickButton3)) // Button A
            {
                ClickCurrentButton();
            }
        }
    }

    void OnEnable()
    {
        currentIndex = 0;
        UpdateButtonColors();
    }

    void CycleToNextButton()
    {
        if (dashboardButtons.Length == 0) return;

        currentIndex++;
        if (currentIndex >= dashboardButtons.Length) currentIndex = 0;

        UpdateButtonColors();
    }

    void ClickCurrentButton()
    {
        if (dashboardButtons.Length > 0 && dashboardButtons[currentIndex] != null)
        {
            dashboardButtons[currentIndex].onClick.Invoke();
        }
    }

    void UpdateButtonColors()
    {
        for (int i = 0; i < dashboardButtons.Length; i++)
        {
            if (dashboardButtons[i] != null)
            {
                ColorBlock colors = dashboardButtons[i].colors;
                colors.normalColor = (i == currentIndex) ? highlightedColor : normalColor;
                dashboardButtons[i].colors = colors;
            }
        }

        // 🪄 THE DEADZONE SCROLL MATH
        if (menuScrollRect != null && dashboardButtons.Length > visibleButtonsOnScreen)
        {
            // Calculate how much extra room we actually have to scroll
            int maxScrollIndex = dashboardButtons.Length - visibleButtonsOnScreen;
            
            // Keeps the scrollbar perfectly still until you reach the middle/bottom of the visible list!
            int clampedIndex = Mathf.Clamp(currentIndex - (visibleButtonsOnScreen / 2), 0, maxScrollIndex);
            
            float scrollMath = 1f - ((float)clampedIndex / maxScrollIndex);
            menuScrollRect.verticalNormalizedPosition = scrollMath;
        }
    }
}