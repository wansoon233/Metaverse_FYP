using UnityEngine;
using UnityEngine.InputSystem; // This Library is required now!

public class CursorManager : MonoBehaviour
{
    private bool isCursorLocked = true;

    void Start()
    {
        LockCursor();
    }

    void Update()
    {
        // The NEW way to check for the "Left Alt" key
        if (Keyboard.current != null && Keyboard.current.leftAltKey.wasPressedThisFrame)
        {
            isCursorLocked = !isCursorLocked; // Flip the state

            if (isCursorLocked)
            {
                LockCursor();
            }
            else
            {
                UnlockCursor();
            }
        }
    }

    void LockCursor()
    {
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
        Debug.Log("Cursor Locked (Walk Mode)");
    }

    void UnlockCursor()
    {
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
        Debug.Log("Cursor Unlocked (Dashboard Mode)");
    }
}