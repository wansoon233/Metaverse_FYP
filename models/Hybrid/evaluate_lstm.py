import sys
import gymnasium as gym
import sinergym
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import logging
import os

# ==========================================
# 0. CONFIGURATION
# ==========================================
logging.getLogger('sinergym').setLevel(logging.WARNING)
print("🚀 Starting Q1 Master's Level Time-Series Cross-Validation...", flush=True)

KL_WEATHER_PATH = '/home/wansoon/Desktop/FYP_Metaverse/sinergym_source/sinergym/data/weather/KualaLumpur.epw' 
TIMESTEPS_FULL_YEAR = 35040 
INDOOR_TEMP_INDEX = 9
SEQ_LENGTH = 24 # The LSTM looks at the past 6 hours (24 steps)

# ==========================================
# 1. THE PYTORCH LSTM FORECASTER
# ==========================================
class SupervisedThermalLSTM(nn.Module):
    def __init__(self, input_size=17, hidden_size=128): 
        super(SupervisedThermalLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True, num_layers=2) 
        self.linear = nn.Linear(hidden_size, 1)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        prediction = self.linear(lstm_out[:, -1, :]) 
        return prediction

# ==========================================
# 2. DATA COLLECTION LOOP
# ==========================================
def main():
    env = gym.make('Eplus-5zone-mixed-continuous-v1', weather_files=KL_WEATHER_PATH)
    try: env.unwrapped.simulator.display_progress = False
    except: pass

    obs, info = env.reset(seed=42)
    raw_states, target_temps = [], []

    print("⏳ Collecting Full Year Building Physics Data...", flush=True)
    for step in range(TIMESTEPS_FULL_YEAR):
        action = env.action_space.sample() 
        next_obs, reward, terminated, truncated, info = env.step(action)
        
        raw_states.append(obs)
        target_temps.append(next_obs[INDOOR_TEMP_INDEX])
        
        obs = next_obs
        if terminated or truncated: break

    env.close()

    # ==========================================
    # 3. CHRONOLOGICAL DATA SPLITTING (70/20/10)
    # ==========================================
    print("✂️ Splitting Time-Series Data (70% Train, 20% Val, 10% Test)...", flush=True)
    scaler = MinMaxScaler()
    raw_states_scaled = scaler.fit_transform(raw_states)

    X, y = [], []
    for i in range(len(raw_states_scaled) - SEQ_LENGTH):
        X.append(raw_states_scaled[i : i + SEQ_LENGTH])
        y.append(target_temps[i + SEQ_LENGTH - 1])

    X = torch.tensor(np.array(X), dtype=torch.float32)
    y = torch.tensor(np.array(y), dtype=torch.float32).view(-1, 1)

    # NON-RANDOM CHRONOLOGICAL SPLITTING (As requested by supervisor)
    total_samples = len(X)
    train_end = int(total_samples * 0.70)
    val_end = int(total_samples * 0.90)

    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]

    # ==========================================
    # 4. TRAINING THE LSTM WITH VALIDATION
    # ==========================================
    num_sensors = env.observation_space.shape[0] 
    model = SupervisedThermalLSTM(input_size=num_sensors)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    EPOCHS = 10
    BATCH_SIZE = 64

    print("🧠 Training PyTorch LSTM Forecaster...", flush=True)
    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0
        indices = torch.randperm(len(X_train)) # Shuffle batches inside training only
        for i in range(0, len(X_train), BATCH_SIZE):
            batch_idx = indices[i : i + BATCH_SIZE]
            predictions = model(X_train[batch_idx])
            loss = criterion(predictions, y_train[batch_idx])
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        # VALIDATION CHECK
        model.eval()
        with torch.no_grad():
            val_preds = model(X_val)
            val_loss = criterion(val_preds, y_val).item()
            
        print(f"   Epoch {epoch+1}/{EPOCHS} | Train Loss: {epoch_loss/len(X_train):.5f} | Val Loss: {val_loss:.5f}")

    # ==========================================
    # 5. FINAL TESTING (THE UNSEEN 10%)
    # ==========================================
    print("🎯 Evaluating on Unseen Test Set (Final 10%)...", flush=True)
    model.eval()
    with torch.no_grad():
        test_predictions = model(X_test).numpy()
        
    test_actuals = y_test.numpy()

    mae = mean_absolute_error(test_actuals, test_predictions)
    rmse = np.sqrt(mean_squared_error(test_actuals, test_predictions))

    print(f"\n--- Master's Validation Results ---")
    print(f"Test Set MAE (Mean Absolute Error):  {mae:.3f} °C")
    print(f"Test Set RMSE (Root Mean Squared):   {rmse:.3f} °C")

    # GRAPHING
    plt.figure(figsize=(18, 5)) 
    plt.plot(test_actuals, label='Actual Building Temperature (°C)', color='blue', linewidth=1.5, alpha=0.8)
    plt.plot(test_predictions, label='LSTM Forecast (°C)', color='red', linewidth=1.0, alpha=0.8)
    
    plt.title("Time-Series Forecasting Accuracy on Unseen Test Data (Final 10%)", fontsize=14, fontweight='bold')
    plt.xlabel("Timestep (15-Minute Intervals)", fontsize=12)
    plt.ylabel("Indoor Temperature (°C)", fontsize=12)
    plt.legend(loc="upper right")
    plt.grid(True, linestyle="--", alpha=0.6)

    save_path = "/home/wansoon/Desktop/FYP_Metaverse/models/Hybrid/results/validation_plot.pdf"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, format="pdf", bbox_inches="tight")
    print(f"✅ Saved Line Graph to {save_path}")

if __name__ == "__main__":
    main()
