using UnityEngine;

public class SmartHeaterVisuals : MonoBehaviour
{
    [Header("Drag all Heater Mist effects here")]
    public ParticleSystem[] heatMistParticles;

    public void SetHeaterState(bool isOn)
    {
        foreach (ParticleSystem mist in heatMistParticles)
        {
            if (mist == null) continue; 

            if (isOn)
            {
                if (!mist.isPlaying) mist.Play();
            }
            else
            {
                mist.Stop();
            }
        }
    }
}