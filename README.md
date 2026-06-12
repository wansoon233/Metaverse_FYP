# 🏡 Metaverse-Ready IoT Smart Home Interface
### Energy & Comfort Control using Hybrid LSTM-PPO-RBC Framework

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![RL](https://img.shields.io/badge/AI-Hybrid%20RL-green) ![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Unity-orange)

## 📖 Project Overview
This repository contains the source code, hardware implementation scripts, and model evaluation files for my Final Year Project (FYP). The project integrates Deep Reinforcement Learning (DRL) with a Metaverse Digital Twin to optimize HVAC energy consumption while maintaining strict occupant thermal comfort boundaries.

The core innovation is a **Hybrid LSTM-PPO-RBC agent**, a multi-hierarchical control system that bridges the gap between virtual simulation environments and physical edge hardware. By combining the predictive memory of an LSTM, the strategic optimization capabilities of PPO, and the deterministic safety guarantees of a Rule-Based Control (RBC) Safety Shield, this architecture achieves precise, real-time temperature regulation on low-cost IoT hardware (Raspberry Pi/ESP32) without risking thermal runaway or mechanical stress. 

## 🚀 Key Features
* 🌐 **Metaverse Digital Twin** — Unity 6-based immersive 3D interface with real-time bidirectional MQTT synchronisation. Manual overrides from the Metaverse interface reach physical GPIO in 16.34 ms (below the 50 ms XR threshold).
* ⚡ **Edge-First Architecture** — Full AI inference pipeline runs on Raspberry Pi 4. Zero cloud dependency. Survives complete network outages (validated: 12-minute router shutdown test).
* 🛡️ **Sim-to-Real Validated** — Pre-trained in Sinergym (EnergyPlus), deployed on physical HIL testbed. Sim-to-Real CZCR gap: only 1.94%.
* 🌍 **Cross-Regional** — Zero-shot generalisation tested across New York (temperate), Kuala Lumpur (tropical), and Tokyo (subtropical) climate datasets.
* 📊 **Energy Savings** — 31.2% less energy than physical RBC baseline, confirmed by ACS712 real-time current measurements.
* 🔒 **Fault Tolerant** — Zero thermal violations under 30% simulated packet loss (vs 19.3% failure rate for cloud-dependent baselines).

## 🛠️ Tech Stack
* **Simulation Environment:** Sinergym (EnergyPlus 5-Zone Building Profile)
* **Deep Learning Framework:** Stable-Baselines3 (RecurrentPPO, PPO), Gymnasium, PyTorch
* **Hardware Layer:** Raspberry Pi 4 (Edge Server Core), ESP32 Nodes (Sensors)
* **Communication Pipeline:** MQTT (Mosquitto Broker)
* **3D Modeling & Visualization:** Blender (Asset Design), Unity Engine (Metaverse Interface)

## ⚙️ Installation 

1. **Clone the Repository & Initialize Environment**
   ```bash
   git clone [https://github.com/wansoon233/Metaverse_FYP.git](https://github.com/wansoon233/Metaverse_FYP.git)
   cd Metaverse_FYP
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate

2. **Install Python Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt

4. **Install EnergyPlus Engine (Required for Sinergym Simulation)**
   Sinergym requires the core EnergyPlus simulation backend installed on your host system to compute building thermodynamics:
   1. Download EnergyPlus 23.1.0 from the Official EnergyPlus Releases Page.
   2. Install the package to your local environment.
   3. Export the path variable to your terminal configuration file:
      
   ```bash
   export ENERGYPLUS_PATH="/usr/local/EnergyPlus-23-1-0/"

## 🎮 Setting up the Unity Metaverse Digital Twin
The Metaverse interface is built using Unity 6 and communicates with the physical hardware via the M2MQTT library. Follow these steps to import and run the 3D Digital Twin:
1. **Prerequisites**
   1. Download and install Unity Hub.
   2. Install Unity 6.
   3. Ensure your Mosquitto MQTT Broker is running on your Raspberry Pi.
2. **Import the Project**
   1. Open Unity Hub.
   2. Click on Add (or "Open") -> Add project from disk
   3. Navigate to the cloned repository folder and select the Unity_Metaverse_Interface folder (or whatever your specific Unity folder is named).
   4. Wait for Unity to import the assets, materials, and scripts. (Note: The first import may take a few minutes as Unity builds the library).
3. **Configure the MQTT Connection (Crucial Step)**
   For the Digital Twin to talk to your physical Raspberry Pi, you must update the MQTT broker IP address in the Unity scripts to match your local network.
   1. In the Unity Editor, go to the Project window and open your Scripts folder.
   2. Open the main MQTT controller script (SmartDevice.cs).
   3. Locate the broker address variable:
      ```bash
      // Change this to the IP address of your Raspberry Pi
      public string brokerAddress = "192.168.1.XXX";
    4. Save the script and return to Unity.
4. **Run the Metaverse Interface**
   1. In the Project window, navigate to the Scenes folder.
   2. Double-click the Main_SmartHome scene to open it.
   3. Press the Play (▶) button at the top of the Unity Editor.
   4. You should see "MQTT Connected" in the Unity Console, and your 3D digital twin will now respond in real-time to your physical ESP32 sensors!

## 📜 License
This repository and its assets are developed as part of a university graduation thesis and are intended strictly for academic evaluation, research peer review, and reproducibility tracking.
