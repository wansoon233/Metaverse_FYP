using UnityEngine;

[RequireComponent(typeof(Canvas))]
public class AutoCanvasCamera : MonoBehaviour
{
    void OnEnable()
    {
        // 1. Grab the Canvas component attached to this object
        Canvas myCanvas = GetComponent<Canvas>();

        // 2. Automatically find whichever camera is currently tagged as "MainCamera"
        if (Camera.main != null)
        {
            myCanvas.worldCamera = Camera.main;
        }
        else
        {
            Debug.LogWarning("No camera tagged 'MainCamera' was found for the Canvas!");
        }
    }
}