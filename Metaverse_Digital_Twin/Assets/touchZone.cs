using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Events;

public class FullScreenSwipe : MonoBehaviour
{
    [System.Serializable]
    public class SwipeEvent : UnityEvent<Vector2> { }

    [Header("Screen Zone (0 = left edge, 1 = right edge)")]
    [Range(0f, 1f)] public float zoneStartX = 0.5f;
    [Range(0f, 1f)] public float zoneEndX   = 1.0f;

    [Header("Settings")]
    public float sensitivity    = 0.2f;
    public bool  horizontalOnly = false;
    public bool  invertX        = false;
    [Range(1f, 20f)] public float smoothing = 8f;

    [Header("State")]
    public bool inputBlocked = false;

    [Header("Output")]
    public SwipeEvent onSwipeDelta;

    private int     activeTouchId = -1;
    private Vector2 lastTouchPos;
    private Vector2 smoothedDelta;

    void Update()
    {
        if (inputBlocked) return;

        if (Input.touchCount > 0)
            HandleTouch();
        else
            HandleMouse();
    }

    void HandleTouch()
    {
        for (int i = 0; i < Input.touchCount; i++)
        {
            Touch touch = Input.GetTouch(i);

            if (touch.phase == TouchPhase.Began)
            {
                if (activeTouchId != -1) continue;
                if (EventSystem.current.IsPointerOverGameObject(touch.fingerId)) continue;

                float nx = touch.position.x / Screen.width;
                if (nx < zoneStartX || nx > zoneEndX) continue;

                activeTouchId = touch.fingerId;
                lastTouchPos  = touch.position;
            }
            else if (touch.phase == TouchPhase.Moved && touch.fingerId == activeTouchId)
            {
                SendDelta(touch.position - lastTouchPos);
                lastTouchPos = touch.position;
            }
            else if ((touch.phase == TouchPhase.Ended || touch.phase == TouchPhase.Canceled)
                      && touch.fingerId == activeTouchId)
            {
                ClearInput();
            }
        }
    }

    void HandleMouse()
    {
        if (Input.GetMouseButtonDown(0))
        {
            if (EventSystem.current.IsPointerOverGameObject()) return;
            float nx = Input.mousePosition.x / Screen.width;
            if (nx < zoneStartX || nx > zoneEndX) return;

            activeTouchId = 0;
            lastTouchPos  = Input.mousePosition;
        }
        else if (Input.GetMouseButton(0) && activeTouchId == 0)
        {
            SendDelta((Vector2)Input.mousePosition - lastTouchPos);
            lastTouchPos = Input.mousePosition;
        }
        else if (Input.GetMouseButtonUp(0) && activeTouchId == 0)
        {
            ClearInput();
        }
    }

    void SendDelta(Vector2 rawDelta)
    {
        Vector2 delta = rawDelta * sensitivity;
        if (horizontalOnly) delta.y = 0f;
        if (invertX)        delta.x = -delta.x;

        smoothedDelta = Vector2.Lerp(smoothedDelta, delta, smoothing * Time.deltaTime);
        onSwipeDelta.Invoke(smoothedDelta);
    }

    void ClearInput()
    {
        activeTouchId = -1;
        smoothedDelta = Vector2.zero;
        onSwipeDelta.Invoke(Vector2.zero);
    }

    // ── Called by TabletController ────────────────────────────────────────────
    public void BlockInput()
    {
        inputBlocked = true;
        ClearInput();
    }

    public void UnblockInput()
    {
        inputBlocked = false;
    }
}