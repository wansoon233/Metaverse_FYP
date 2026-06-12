#!/bin/bash

# --- CONFIGURATION ---
# Exit immediately if a command exits with a non-zero status (Error safety)
set -e 

echo "========================================================"
echo "🚀 FYP METAVERSE: AUTOMATED EXPERIMENT RUNNER"
echo "========================================================"
echo "Date: $(date)"
echo "Mode: Full Training & Evaluation (200k Steps)"
echo "========================================================"
echo ""

# 1. ACTIVATE VIRTUAL ENVIRONMENT
echo "🔵 [1/4] Activating Virtual Environment..."
source venv/bin/activate
echo "✅ Environment Active."
echo ""

# 2. CLEAN OLD JUNK (Safety First)
echo "🧹 [2/4] Pre-Cleaning Simulation Junk..."
rm -rf Eplus-5zone-mixed-continuous-v1-res*
rm -rf Eplus-5zone-mixed-discrete-v1-res*
echo "✅ Workspace Clean."
echo ""

# 3. RUN BASELINES (RBC & PID)
echo "🔵 [3/4] Running Classical Baselines (RBC & PID)..."
# (Assuming you have the run_baselines.py we discussed earlier)
# If you don't have this file, skip this line or ask me to generate it.
if [ -f "models/Baselines/run_baselines.py" ]; then
    python models/Baselines/run_baselines.py
else
    echo "⚠️  Baseline script not found. Skipping."
fi
echo "✅ Baselines Done."
echo ""

# 4. RUN PPO (The Platinum Script)
echo "🔵 [4/4] Running PPO Training (Platinum Edition)..."
python models/PPO/train_ppo_robust.py
echo "✅ PPO Done."
echo ""

# 5. RUN DQN (The Updated Script)
echo "🔵 [5/4] Running DQN Training..."
python models/DQN/train_dqn.py
echo "✅ DQN Done."
echo ""

# 6. FINAL CLEANUP
echo "🧹 [Final] Cleaning remaining simulation folders..."
rm -rf Eplus-5zone-mixed-continuous-v1-res*
rm -rf Eplus-5zone-mixed-discrete-v1-res*

echo "========================================================"
echo "🏆 ALL EXPERIMENTS COMPLETED SUCCESSFULLY"
echo "   Results are stored in: models/*/results/"
echo "========================================================"
