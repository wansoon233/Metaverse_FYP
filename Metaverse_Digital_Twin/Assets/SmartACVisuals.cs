using UnityEngine;

public class SmartACVisuals : MonoBehaviour
{
    [Header("Drag all 4 ColdAirMist effects here")]
    // The [] brackets turn this into an Array (a list of slots)
    public ParticleSystem[] coldAirParticles;

    public void SetACSpeed(int speedLevel)
    {
        // This 'foreach' loop goes through every single vent one by one
        foreach (ParticleSystem vent in coldAirParticles)
        {
            if (vent == null) continue; // Skip if a slot is accidentally empty

            var emission = vent.emission;

            if (speedLevel == 0) // OFF
            {
                vent.Stop();
            }
            else // ON (Low, Med, High)
            {
                if (!vent.isPlaying) vent.Play();

                if (speedLevel == 1) emission.rateOverTime = 10f;      // LOW
                else if (speedLevel == 2) emission.rateOverTime = 30f; // MEDIUM
                else if (speedLevel == 3) emission.rateOverTime = 70f; // HIGH
            }
        }
    }
}