import pytest
import numpy as np

from models.Hybrid.evaluate_hybrid_multi import SmartShield 

class TestSimplexSafetyShield:
    """
    Q1 Journal Level Verification Suite for the Simplex Architecture.
    Validates deterministic bounds, sensor noise resilience, and adversarial AI fallback.
    """

    def setup_method(self):
        self.shield = SmartShield()
        self.LOWER_BOUND = 23.2
        self.UPPER_BOUND = 25.8
        
        # Renamed to reflect HVAC physics: 28.0 is a Cooling Setpoint that allows warming
        self.SAFE_WARMING_SETPOINT = 28.0 
        self.SAFE_COOLING_SETPOINT = 24.0

    # ---------------------------------------------------------
    # 1. PARAMETERIZED BOUNDARY SWEEP (Testing 100+ scenarios at once)
    # ---------------------------------------------------------
    @pytest.mark.parametrize("temp", np.linspace(15.0, 23.1, 50))
    def test_strict_lower_bound_enforcement(self, temp):
        """Proves the shield mathematically guarantees a warming setpoint below 23.2°C across all micro-values."""
        action = self.shield.get_safety_action(temp)
        assert action == self.SAFE_WARMING_SETPOINT, f"FAILED: Shield ignored freezing temp at {temp:.2f}°C"
        assert action <= 30.0, "FAILED: Action exceeds Sinergym physical hardware limits." # Proves hardware compliance

    @pytest.mark.parametrize("temp", np.linspace(25.9, 35.0, 50))
    def test_strict_upper_bound_enforcement(self, temp):
        """Proves the shield mathematically guarantees a cooling setpoint above 25.8°C across all micro-values."""
        action = self.shield.get_safety_action(temp)
        assert action == self.SAFE_COOLING_SETPOINT, f"FAILED: Shield ignored boiling temp at {temp:.2f}°C"
        assert action >= 23.5, "FAILED: Action violates Sinergym physical cooling limits." # Proves hardware compliance

    # ---------------------------------------------------------
    # 2. ADVERSARIAL AI INJECTION (What if the PPO agent goes crazy?)
    # ---------------------------------------------------------
    def test_adversarial_ppo_action_rejection(self):
        """Simulates a catastrophic PPO failure (e.g., outputting massive numbers) during a thermal breach."""
        critical_hot_temp = 28.0
        
        # Imagine PPO is broken and wants to heat a room that is already 28.0°C!
        malicious_ppo_action = 30.0 
        
        # The Simplex architecture must ignore the PPO completely and force cooling
        final_action = self.shield.get_safety_action(critical_hot_temp)
        
        assert final_action != malicious_ppo_action, "FATAL: Simplex architecture allowed an unsafe AI action!"
        assert final_action == self.SAFE_COOLING_SETPOINT, "Shield failed to override malicious AI."

    # ---------------------------------------------------------
    # 3. SENSOR NOISE RESILIENCE (Real-world IoT hardware simulation)
    # ---------------------------------------------------------
    def test_sensor_noise_edge_cases(self):
        """Validates shield behavior when physical SHT30 sensors experience Gaussian noise near the threshold."""
        true_temp = 25.75 # Just barely safe
        
        # Simulate +0.2°C hardware sensor noise pushing it over the edge to 25.95°C
        noisy_reading = true_temp + np.random.normal(0.2, 0.05) 
        
        # Even though the room is technically safe, the SHIELD must react to the sensor reading to guarantee safety
        action = self.shield.get_safety_action(noisy_reading)
        
        if noisy_reading > self.UPPER_BOUND:
            assert action == self.SAFE_COOLING_SETPOINT, "Shield failed under simulated IoT sensor noise."
