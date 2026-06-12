using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

[RequireComponent(typeof(CharacterController))]
public class VRSimpleWalk : MonoBehaviour
{
    public float speed = 2.0f;
    public Transform vrCamera; 

    [Header("Controller Setup")]
    public bool holdControllerSideways = true; // Flips the axes for you!

    private CharacterController controller;

    void Start()
    {
        controller = GetComponent<CharacterController>();
    }

    void Update()
    {
        float x = 0f;
        float z = 0f;

        #if ENABLE_INPUT_SYSTEM
        if (Gamepad.current != null)
        {
            Vector2 dpadInput = Gamepad.current.dpad.ReadValue();
            
            if (holdControllerSideways)
            {
                // Mathematically rotates the D-Pad 90 degrees!
                // Pushing physical "Up" (y=1) moves you Right (x=1)
                x = dpadInput.y;
                // Pushing physical "Left" (x=-1) moves you Forward (z=1)
                z = -dpadInput.x; 
            }
            else
            {
                x = dpadInput.x;
                z = dpadInput.y;
            }
        }
        #endif

        if ((x != 0 || z != 0) && vrCamera != null)
        {
            Vector3 forward = vrCamera.forward;
            Vector3 right = vrCamera.right;
            
            forward.y = 0; 
            right.y = 0;
            forward.Normalize();
            right.Normalize();

            Vector3 moveDirection = (right * x) + (forward * z);
            controller.Move(moveDirection * speed * Time.deltaTime);
        }

        if (!controller.isGrounded)
        {
            controller.Move(new Vector3(0, -9.8f * Time.deltaTime, 0));
        }
    }
}