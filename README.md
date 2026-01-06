# 🏡 Metaverse-Ready IoT Smart Home Interface
### Energy & Comfort Control using Hybrid LSTM-PPO-PID Framework

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![RL](https://img.shields.io/badge/AI-Hybrid%20RL-green) ![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Unity-orange)

## 📖 Project Overview
This project is my **Final Year Project (FYP)** that integrates **Deep Reinforcement Learning (DRL)** with a **Metaverse Digital Twin** to optimize HVAC energy consumption while maintaining thermal comfort.

The core innovation is a **Hybrid LSTM-PPO-PID agent**, a multi-hierarchical control system that bridges the gap between virtual simulation (Sinergym) and physical hardware. By combining the predictive power of **LSTM**, the strategic decision-making of **PPO**, and the stability of **PID**, this system achieves precise real-time temperature regulation on low-cost IoT hardware (Raspberry Pi/ESP32).

## 🚀 Key Features
- **🧠 Hybrid LSTM-PPO-PID Architecture:**
  - **LSTM (Long Short-Term Memory):** Predicts future thermal loads based on historical sensor data.
  - **PPO (Proximal Policy Optimization):** Makes high-level energy-saving decisions.
  - **PID (Proportional-Integral-Derivative):** Ensures smooth, stable actuator control and eliminates steady-state error.
- **🛡️ Smart Energy Shield:** A deterministic safety layer that prevents overheating even if the neural network fails.
- **🌐 Metaverse Integration:** Two-way synchronization between a Unity-based Digital Twin and physical IoT sensors via **MQTT**.
- **⚡ 100% Safety Compliance:** Achieved **Zero Overshoot** (>26°C) during validation testing.

## 🛠️ Tech Stack
- **Simulation:** Sinergym (EnergyPlus 5-Zone)
- **AI Framework:** Stable-Baselines3 (PPO, RecurrentPPO), Gymnasium
- **Hardware:** Raspberry Pi 4 (Edge Server), ESP32 (Sensors/Relays)
- **Communication:** MQTT (Mosquitto Broker)
- **3D Modelling** Blender
- **Visualization:** Unity Engine (Metaverse Interface)

## 📂 Repository Structure
```text
├── models/               # Trained AI Brains (.zip) & Result CSVs
│   ├── Hybrid/           # Proposed LSTM-PPO-PID Model
│   ├── PPO/              # Standard Baseline
│   └── PID/              # Classical Control Baseline
├── thesis_plots/         # Generated Graphs for Report (Chapter 4)
├── table_generate.py     # Main script for generating Table 4.1 & Graphs
├── train_hybrid.py       # Script to train the Hybrid agent
└── requirements.txt      # Python dependencies
```

## 📊 Results Summary
The proposed **Hybrid LSTM-PPO** model was benchmarked against standard PPO and PID controllers over a 1-year simulation cycle.

| Algorithm | Accuracy | F1-Score | Energy (kWh) | Latency |
|:----------|:--------:|:--------:|:------------:|:-------:|
| **PID** | 94.73%   | 0.97     | 34,796       | 0.05 ms |
| **PPO** | 99.46%   | 1.00     | 36,113       | 0.38 ms |
| **Hybrid**| **100%** | **1.00** | 37,873       | 0.98 ms |

*Note: The Hybrid model accepts a slight increase in energy (+5%) to guarantee **zero thermal violations**, prioritizing user safety.*

## ⚙️ Installation & Usage

1. **Clone the Repo**
   ```bash
   git clone [https://github.com/wansoon233/Metaverse_FYP.git](https://github.com/wansoon233/Metaverse_FYP.git)
   cd Metaverse_FYP

2. **Install Dependencies**
  '''bash
  pip install -r requirement.txt

3. **Run Validation (Generate Results)**
  '''bash
  python table_generate.py


📜 License
This project is for academic purposes.
