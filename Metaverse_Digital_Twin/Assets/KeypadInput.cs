using UnityEngine;
using UnityEngine.InputSystem;

public class KeypadInput : MonoBehaviour
{
    [Header("Settings")]
    public float interactionDistance = 3.0f;

    void Update()
    {
        // --- 🔒 SAFETY CHECK ---
        // If the cursor is LOCKED (Walk Mode), stop here.
        // We only want to click when the cursor is FREE (Dashboard/Alt Mode).
        if (Cursor.lockState == CursorLockMode.Locked)
        {
            return; 
        }

        // --- 🖱️ CLICK LOGIC ---
        // Check for Left Click
        if (Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame)
        {
            TryClickButton();
        }
    }

    void TryClickButton()
    {
        Ray ray = Camera.main.ScreenPointToRay(Mouse.current.position.ReadValue());
        RaycastHit hit;

        if (Physics.Raycast(ray, out hit, interactionDistance))
        {
            Keypad3DButton button = hit.collider.GetComponent<Keypad3DButton>();

            if (button != null)
            {
                button.keypadBrain.PressButton(button.myValue);
            }
        }
    }
}